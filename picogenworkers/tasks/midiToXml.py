"""Convert performance MIDI (piano transcription output) into engravable MusicXML.

This module turns the *performance* MIDI produced by an automatic-music-transcription
model into a *score*: a single two-staff piano part with a beat grid, meter, key
signature, quantized rhythms, ties across barlines, chords, up to two voices per
staff, beams, tuplets, dynamics and sustain-pedal marks.

The pipeline is a chain of pure functions over small dataclasses::

    parse_midi        raw note/CC extraction (pretty_midi)
    choose_grid       beat grid: file tempo map vs. DP-tracked estimate
    detect_meter      4/4 or 3/4 plus the pickup phase
    quantize          per-beat subdivision snapping (duple + triplet)
    assign_hands      staff 1 / staff 2 split
    separate_voices   <=2 voices per staff
    detect_key        Krumhansl-Schmuckler + line-of-fifths spelling
    plan_measures     barline splitting, rest filling, tuplet grouping
    decompose         metric-strength duration decomposition + ties
    assign_beams      per-beat beam state machine
    build_score       MusicXML 3.1 score-partwise DOM
    check_invariants  re-walk the finished DOM and prove it is well formed

Runtime dependencies are limited to ``pretty_midi``, ``numpy`` and the standard
library.  ``mido`` is imported lazily and only by ``--selftest``.

Public API::

    convert_midi_to_xml(midi_file_path, output_path, job_id=None,
                        sheet_music_title=None) -> str

Command line::

    python midiToXml.py <input.mid> <output.musicxml> [title]
    python midiToXml.py --selftest
    python midiToXml.py --check <file.musicxml>
"""

from __future__ import annotations

import datetime as _dt
import logging
import math
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pretty_midi

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Ticks per quarter note used throughout the emitted score.  480 is divisible by
#: 2, 3, 4, 6 and 8, so every subdivision this module supports lands on an
#: integer tick and ``<duration>`` never has to be rounded.
DIVS = 480

#: Krumhansl-Schmuckler key profiles (tonic-relative pitch class weights).
KS_MAJOR = (6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88)
KS_MINOR = (6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17)

#: Duple (non-tuplet) durations -> (MusicXML note type, number of dots).
#: Only single dots are used; dotted rests and double dots are never emitted.
DUPLE_DISPLAY: Dict[int, Tuple[str, int]] = {
    1920: ("whole", 0),
    1440: ("half", 1),
    960: ("half", 0),
    720: ("quarter", 1),
    480: ("quarter", 0),
    360: ("eighth", 1),
    240: ("eighth", 0),
    180: ("16th", 1),
    120: ("16th", 0),
    60: ("32nd", 0),
}

#: Tuplet durations per subdivision -> (type, dots).  A 3:2 group spanning one
#: beat has unit 160 (triplet eighth); a 3:2 group spanning half a beat has unit
#: 80 (triplet sixteenth).  Full-span members are emitted as plain duple notes
#: instead, so the whole-group duration deliberately has no entry here.
TUPLET_DISPLAY: Dict[int, Dict[int, Tuple[str, int]]] = {
    3: {160: ("eighth", 0), 320: ("quarter", 0)},
    6: {80: ("16th", 0), 160: ("eighth", 0)},
}

#: Metric levels per beats-per-bar, strongest first.  A position's metric
#: strength is the largest level that divides it.  3/4 deliberately has no
#: half-bar level: there is no 960-tick division point in a three-beat bar.
METRIC_LEVELS: Dict[int, Tuple[int, ...]] = {
    4: (1920, 960, 480, 240, 120, 60, 20),
    3: (1440, 480, 240, 120, 60, 20),
}

#: Complexity penalty (seconds of equivalent alignment error) for choosing each
#: subdivision, so a beat only becomes a triplet beat if the evidence pays for it.
SUBDIV_PENALTY: Dict[int, float] = {1: 0.0, 2: 0.010, 4: 0.025, 3: 0.045, 6: 0.070, 8: 0.080}

#: Candidate subdivisions, in increasing complexity order.
SUBDIVS: Tuple[int, ...] = (1, 2, 4, 3, 6, 8)

#: Upper velocity bound (inclusive) -> dynamic mark.
DYNAMIC_THRESHOLDS: Tuple[Tuple[int, str], ...] = (
    (33, "pp"),
    (49, "p"),
    (64, "mp"),
    (80, "mf"),
    (96, "f"),
    (127, "ff"),
)

#: Playback velocity written into <sound dynamics="..."> for each mark.
DYNAMIC_SOUND: Dict[str, int] = {"pp": 40, "p": 54, "mp": 68, "mf": 83, "f": 97, "ff": 111}

#: Line-of-fifths index of each natural step (F=-1 ... B=5).  Adding 7 per sharp
#: and subtracting 7 per flat gives a total ordering of every spelling.
LOF_BASE: Dict[str, int] = {"F": -1, "C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5}

#: Pitch class of each natural step.
STEP_PC: Dict[str, int] = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

#: Diatonic index of each staff's bottom and top line, where a diatonic index is
#: ``octave * 7 + offset-within-the-octave`` - one unit per notehead position, so
#: the distance between two staff lines is exactly 2.  Treble spans E4..F5, bass
#: G2..A3.  Anything outside these needs a ledger line for every 2 units past the
#: edge, which is what makes the range a cost rather than just a fact.
STAFF_EXTENT: Dict[int, Tuple[int, int]] = {1: (30, 38), 2: (18, 26)}

#: Diatonic offset of each pitch class, spelled naturally (C# reads as C, Eb as E).
_PC_DIATONIC: Tuple[int, ...] = (0, 0, 1, 2, 2, 3, 4, 4, 5, 5, 6, 6)

#: Every spelling this module can emit, as (step, alter) -> line-of-fifths index.
SPELLINGS: Tuple[Tuple[str, int], ...] = tuple(
    (step, alter) for step in "CDEFGAB" for alter in (-2, -1, 0, 1, 2)
)

#: Legal child order of <note> in MusicXML 3.1 (the subset this module emits).
NOTE_CHILD_ORDER: Tuple[str, ...] = (
    "chord",
    "pitch",
    "rest",
    "duration",
    "tie",
    "voice",
    "type",
    "dot",
    "accidental",
    "time-modification",
    "stem",
    "staff",
    "beam",
    "notations",
)

#: Voice numbers per staff.  Globally unique numbering (1,2 / 5,6) is the
#: MuseScore export convention and is what OSMD and musicxml2ly are best tested
#: against.  The mapping never changes mid-piece.
STAFF_VOICES: Dict[int, Tuple[int, int]] = {1: (1, 2), 2: (5, 6)}

# Where a rest sits when two voices share a staff, one line either side of centre
# (centre being B4 in treble, D3 in bass): the stem-up voice above, the stem-down
# voice below, so the two never try to occupy the same space.  Keyed by (staff, stem).
TWO_VOICE_REST_POSITION: Dict[Tuple[int, str], Tuple[str, int]] = {
    (1, "up"): ("D", 5),
    (1, "down"): ("G", 4),
    (2, "up"): ("F", 3),
    (2, "down"): ("B", 2),
}

_BEAM_TYPES: Dict[str, int] = {"eighth": 1, "16th": 2, "32nd": 3}


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


@dataclass
class Settings:
    """Every tunable in one place.  Defaults are what the pipeline ships with."""

    # --- onset envelope / tempo estimation ---
    fps: int = 100
    bpm_min: float = 50.0
    bpm_max: float = 200.0
    prior_center_bpm: float = 105.0
    prior_sigma_log2: float = 0.45
    dp_tightness: float = 100.0

    # --- grid scoring ---
    onset_cluster_s: float = 0.030
    err_clip_s: float = 0.060
    # Subdivision choice gets a looser clip than grid scoring on purpose.  Grid
    # scoring compares whole-piece alignment, where one wild onset must not
    # dominate.  Within a single beat the deviations that matter are systematic:
    # reading a triplet as duple misplaces attacks by a third of a beat, and
    # under the tighter clip that costs the same as an outlier, which is how
    # "no subdivision at all" ends up undercutting a real tuplet.
    subdiv_err_clip_s: float = 0.120
    collision_cost_s: float = 0.045
    triplet_cost_s: float = 0.012
    fine_cost_s: float = 0.010
    tempo_soft_min_bpm: float = 60.0
    tempo_soft_max_bpm: float = 160.0
    tempo_penalty_s: float = 0.035
    grid_margin_s: float = 0.004
    triplet_flip_margin: float = 0.010

    # --- note cleaning ---
    ghost_dur_s: float = 0.05
    ghost_vel: int = 25
    legato_fill_ticks: int = 120
    trunc_max_ticks: int = 240
    trunc_max_frac: float = 0.50

    # --- hands ---
    #: Widest interval one hand is asked to reach at once, in semitones.
    hand_span_semitones: int = 14
    #: Ledger lines' worth of cost per semitone a hand is stretched past that.
    hand_span_penalty: float = 3.0
    #: Ledger lines' worth of cost per semitone a hand's centre shifts between
    #: onsets.  Trades readability for a hand position that stays put: raising it
    #: settles the hands down, lowering it chases the last ledger line.
    hand_move_penalty: float = 0.06

    # --- meter ---
    meter_bias_34: float = 1.15
    meter_bias_34_margin: float = 0.05
    downbeat_bias: float = 0.12

    # --- dynamics ---
    dyn_ema: float = 0.3
    dyn_margin: int = 5
    dyn_min_gap_beats: float = 8.0

    # --- pedal ---
    pedal_on_value: int = 64
    pedal_merge_s: float = 0.10
    pedal_min_s: float = 0.15

    # --- feature flags ---
    emit_wedges: bool = False
    emit_tempo_changes: bool = False
    emit_staccato: bool = False
    emit_accents: bool = False

    # --- safety ---
    strict: bool = True
    max_measures: int = 2000


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class RawNote:
    """A note in wall-clock seconds, exactly as the MIDI file describes it."""

    start: float
    end: float
    pitch: int
    velocity: int


@dataclass
class ParsedMidi:
    notes: List[RawNote]
    pedal: List[Tuple[float, int]]
    tempo_times: np.ndarray
    tempo_bpms: np.ndarray
    time_signatures: List[Tuple[float, int, int]]
    file_beats: np.ndarray
    file_downbeats: np.ndarray
    resolution: int
    end_time: float

    @property
    def suspect_default_tempo(self) -> bool:
        """True when the tempo map carries no information.

        A single 120 BPM event is what every writer emits when it has nothing to
        say.  An auto-written 4/4 time signature is *not* evidence either way, so
        it deliberately does not participate in this test.
        """
        if len(self.tempo_bpms) != 1:
            return False
        return abs(float(self.tempo_bpms[0]) - 120.0) < 0.51


@dataclass
class Grid:
    """A monotone sequence of beat times in seconds, plus where it came from."""

    beat_times: np.ndarray
    source: str

    def to_beats(self, t: float) -> float:
        """Map a wall-clock time to fractional beat position (linear in-beat)."""
        bt = self.beat_times
        if len(bt) < 2:
            return 0.0
        i = int(np.searchsorted(bt, t, side="right")) - 1
        if i < 0:
            ibi = float(bt[1] - bt[0])
            return (t - float(bt[0])) / ibi if ibi > 0 else 0.0
        if i >= len(bt) - 1:
            ibi = float(bt[-1] - bt[-2])
            return (len(bt) - 1) + (t - float(bt[-1])) / ibi if ibi > 0 else float(len(bt) - 1)
        ibi = float(bt[i + 1] - bt[i])
        if ibi <= 0:
            return float(i)
        return i + (t - float(bt[i])) / ibi

    def ibi(self, index: int) -> float:
        """Inter-beat interval around beat ``index``, in seconds."""
        bt = self.beat_times
        if len(bt) < 2:
            return 0.5
        i = min(max(index, 0), len(bt) - 2)
        return float(bt[i + 1] - bt[i])

    def bpm_median(self) -> float:
        bt = self.beat_times
        if len(bt) < 2:
            return 100.0
        diffs = np.diff(bt)
        diffs = diffs[diffs > 1e-6]
        if len(diffs) == 0:
            return 100.0
        return float(60.0 / np.median(diffs))


@dataclass
class QNote:
    """A note quantized onto the tick grid.  ``on``/``off`` are absolute ticks."""

    on: int
    off: int
    pitch: int
    velocity: int
    staff: int = 1

    @property
    def dur(self) -> int:
        return self.off - self.on


@dataclass
class VoiceEvent:
    """One rhythmic slot in one voice: a chord (1+ pitches) or a rest."""

    on: int
    dur: int
    kind: str  # "note" | "rest"
    pitches: Tuple[int, ...] = ()
    velocity: int = 64

    @property
    def off(self) -> int:
        return self.on + self.dur


@dataclass
class Fragment:
    """A single notatable element: what finally becomes one ``<note>`` (or chord)."""

    on: int
    dur: int
    kind: str
    pitches: Tuple[int, ...] = ()
    velocity: int = 64
    tie_in: bool = False
    tie_out: bool = False
    disp_type: Optional[str] = None
    dots: int = 0
    tmod: Optional[Tuple[int, int]] = None
    tuplet_mark: Optional[str] = None  # "start" | "stop" | "both"
    beams: Dict[int, str] = field(default_factory=dict)
    #: pitch -> alter that must be printed as an accidental on this note
    accidentals: Dict[int, int] = field(default_factory=dict)
    #: emit with ``print-object="no"``: fills time but is not engraved
    invisible: bool = False

    @property
    def off(self) -> int:
        return self.on + self.dur


@dataclass
class MeasureCtx:
    """Where a measure starts, how long it is, and what it is called."""

    number: int
    start: int
    length: int
    implicit: bool = False
    beats: int = 4


# ---------------------------------------------------------------------------
# Stage 1 - parse
# ---------------------------------------------------------------------------


def parse_midi(midi_file_path: str, cfg: Settings) -> ParsedMidi:
    """Read a MIDI file into wall-clock notes plus tempo/meter/pedal metadata.

    All non-drum instruments are merged: transcription models sometimes emit two
    tracks for the two hands, and the staff split downstream is more reliable
    than trusting that grouping.  Zero-length notes, ghost notes and same-pitch
    overlaps are removed here so every later stage can assume sane input.
    """
    pm = pretty_midi.PrettyMIDI(str(midi_file_path))

    raw: List[RawNote] = []
    pedal: List[Tuple[float, int]] = []
    for inst in pm.instruments:
        if inst.is_drum:
            continue
        for n in inst.notes:
            if n.end - n.start <= 1e-4:
                continue
            raw.append(RawNote(float(n.start), float(n.end), int(n.pitch), int(n.velocity)))
        for cc in inst.control_changes:
            if cc.number == 64:
                pedal.append((float(cc.time), int(cc.value)))

    if not raw:
        raise ValueError("MIDI file contains no notes")

    dropped_ghosts = 0
    kept: List[RawNote] = []
    for n in raw:
        if (n.end - n.start) < cfg.ghost_dur_s and n.velocity < cfg.ghost_vel:
            dropped_ghosts += 1
            continue
        kept.append(n)
    if kept:
        raw = kept
    if dropped_ghosts:
        logging.info("Dropped %d ghost note(s) (short and quiet)", dropped_ghosts)

    raw.sort(key=lambda n: (n.start, n.pitch))

    # Same-pitch overlaps are physically impossible on a piano and confuse both
    # tie chains and voice assignment: end the earlier note where the later begins.
    last_by_pitch: Dict[int, RawNote] = {}
    clipped = 0
    for n in raw:
        prev = last_by_pitch.get(n.pitch)
        if prev is not None and prev.end > n.start:
            prev.end = max(n.start, prev.start + 1e-3)
            clipped += 1
        last_by_pitch[n.pitch] = n
    if clipped:
        logging.info("Clipped %d same-pitch overlap(s)", clipped)
    raw = [n for n in raw if n.end - n.start > 1e-4]
    if not raw:
        raise ValueError("MIDI file contains no notes")

    pedal.sort(key=lambda ev: ev[0])

    tempo_times, tempo_bpms = pm.get_tempo_changes()
    time_sigs = [
        (float(ts.time), int(ts.numerator), int(ts.denominator))
        for ts in pm.time_signature_changes
    ]

    try:
        file_beats = np.asarray(pm.get_beats(), dtype=float)
    except Exception:  # pragma: no cover - malformed tempo map
        file_beats = np.zeros(0, dtype=float)
    try:
        file_downbeats = np.asarray(pm.get_downbeats(), dtype=float)
    except Exception:  # pragma: no cover
        file_downbeats = np.zeros(0, dtype=float)

    end_time = max(n.end for n in raw)

    parsed = ParsedMidi(
        notes=raw,
        pedal=pedal,
        tempo_times=np.asarray(tempo_times, dtype=float),
        tempo_bpms=np.asarray(tempo_bpms, dtype=float),
        time_signatures=time_sigs,
        file_beats=file_beats,
        file_downbeats=file_downbeats,
        resolution=int(pm.resolution),
        end_time=float(end_time),
    )
    logging.info(
        "Parsed MIDI: %d notes, %.2fs, %d tempo event(s), %d CC64 event(s), PPQ %d",
        len(raw),
        end_time,
        len(parsed.tempo_bpms),
        len(pedal),
        parsed.resolution,
    )
    return parsed


def onset_clusters(
    notes: Sequence[RawNote], window_s: float
) -> List[Tuple[float, int, float]]:
    """Group near-simultaneous onsets.

    Returns ``(time, count, weight)`` per cluster, where ``time`` is the mean
    onset and ``weight`` grows with the loudest note in the cluster.  Clustering
    keeps a ten-note chord from outvoting ten separate melody notes when the beat
    grid is scored.
    """
    if not notes:
        return []
    onsets = sorted((n.start, n.velocity) for n in notes)
    clusters: List[Tuple[float, int, float]] = []
    cur_times: List[float] = [onsets[0][0]]
    cur_vel: int = onsets[0][1]
    for t, v in onsets[1:]:
        if t - cur_times[0] <= window_s:
            cur_times.append(t)
            cur_vel = max(cur_vel, v)
        else:
            clusters.append(
                (
                    sum(cur_times) / len(cur_times),
                    len(cur_times),
                    0.4 + 0.6 * (cur_vel / 127.0),
                )
            )
            cur_times = [t]
            cur_vel = v
    clusters.append(
        (sum(cur_times) / len(cur_times), len(cur_times), 0.4 + 0.6 * (cur_vel / 127.0))
    )
    return clusters


# ---------------------------------------------------------------------------
# Stage 2 - beat grid
# ---------------------------------------------------------------------------


def build_onset_envelope(notes: Sequence[RawNote], end_time: float, cfg: Settings) -> np.ndarray:
    """Velocity-weighted onset salience at ``cfg.fps`` frames per second.

    Bass onsets get a small boost because in piano music the left hand carries
    the beat far more reliably than the melody does.
    """
    n_frames = int(math.ceil(max(end_time, 0.0) * cfg.fps)) + 1
    env = np.zeros(n_frames + 8, dtype=float)
    for note in notes:
        idx = int(round(note.start * cfg.fps))
        if 0 <= idx < len(env):
            weight = 0.5 + 0.5 * (note.velocity / 127.0)
            if note.pitch < 50:
                weight += 0.3
            env[idx] += weight
    np.clip(env, 0.0, 4.0, out=env)
    window = np.hanning(9)
    window = window / window.sum()
    env = np.convolve(env, window, mode="same")
    std = float(env.std())
    if std > 1e-9:
        env = (env - float(env.mean())) / std
    return env


def estimate_period_frames(env: np.ndarray, cfg: Settings) -> Optional[float]:
    """Dominant inter-beat period, in frames, via autocorrelation under a prior.

    The log-normal tempo prior is what keeps autocorrelation from locking onto a
    half- or double-tempo peak, which is the classic failure mode.
    """
    n = len(env)
    lo = int(math.floor(cfg.fps * 60.0 / cfg.bpm_max))
    hi = int(math.ceil(cfg.fps * 60.0 / cfg.bpm_min))
    hi = min(hi, n - 2)
    lo = max(lo, 2)
    if hi <= lo + 1:
        return None

    autocorr = np.correlate(env, env, mode="full")[n - 1 :]
    lags = np.arange(lo, hi + 1)
    bpms = 60.0 * cfg.fps / lags
    prior = np.exp(
        -0.5 * (np.log2(bpms / cfg.prior_center_bpm) / cfg.prior_sigma_log2) ** 2
    )
    scores = np.maximum(autocorr[lo : hi + 1], 0.0) * prior
    best = int(np.argmax(scores))
    if scores[best] <= 0.0:
        return None

    period = float(lags[best])
    if 0 < best < len(scores) - 1:
        y0, y1, y2 = float(scores[best - 1]), float(scores[best]), float(scores[best + 1])
        denom = y0 - 2.0 * y1 + y2
        if abs(denom) > 1e-12:
            shift = 0.5 * (y0 - y2) / denom
            if abs(shift) < 1.0:
                period += shift
    return period


def track_beats_dp(env: np.ndarray, period: float, cfg: Settings) -> Optional[np.ndarray]:
    """Ellis-style dynamic-programming beat tracking.

    Maximises onset salience at beat positions minus a squared-log penalty on
    deviation from the target period.  A single global tempo would accumulate
    phase error under the rubato that transcription MIDI is full of; DP tracking
    follows it instead.
    """
    n = len(env)
    period = max(float(period), 2.0)
    if n < 4 * period:
        return None

    cum = np.zeros(n, dtype=float)
    back = np.full(n, -1, dtype=int)
    for t in range(n):
        hi = int(round(t - 0.5 * period))
        if hi < 0:
            cum[t] = env[t]
            continue
        lo = max(int(round(t - 2.0 * period)), 0)
        if lo > hi:
            cum[t] = env[t]
            continue
        idx = np.arange(lo, hi + 1)
        ratio = np.maximum((t - idx) / period, 1e-6)
        value = cum[lo : hi + 1] - cfg.dp_tightness * (np.log(ratio) ** 2)
        j = int(np.argmax(value))
        cum[t] = env[t] + float(value[j])
        back[t] = lo + j

    end = int(np.argmax(cum))
    beats: List[int] = []
    while end >= 0:
        beats.append(end)
        end = int(back[end])
    beats.reverse()
    if len(beats) < 4:
        return None
    return np.asarray(beats, dtype=float) / cfg.fps


def _extend_beats(beats: np.ndarray, first: float, last: float) -> np.ndarray:
    """Extrapolate a beat sequence outwards so it covers ``[first, last]``."""
    if len(beats) < 2:
        return beats
    out = list(map(float, beats))
    head_ibi = float(np.median(np.diff(beats[: min(5, len(beats))]))) if len(beats) >= 3 else float(
        beats[1] - beats[0]
    )
    tail_ibi = float(np.median(np.diff(beats[-min(5, len(beats)) :]))) if len(beats) >= 3 else float(
        beats[-1] - beats[-2]
    )
    head_ibi = head_ibi if head_ibi > 1e-4 else 0.5
    tail_ibi = tail_ibi if tail_ibi > 1e-4 else 0.5
    guard = 0
    while out[0] > first + 1e-9 and guard < 10000:
        out.insert(0, out[0] - head_ibi)
        guard += 1
    guard = 0
    while out[-1] < last - 1e-9 and guard < 100000:
        out.append(out[-1] + tail_ibi)
        guard += 1
    return np.asarray(out, dtype=float)


def grid_from_file(parsed: ParsedMidi) -> Optional[Grid]:
    """The beat grid the file itself declares, via its tempo map."""
    beats = parsed.file_beats
    if beats is None or len(beats) < 4:
        return None
    beats = np.asarray(sorted(set(round(float(b), 6) for b in beats)), dtype=float)
    if len(beats) < 4 or float(np.min(np.diff(beats))) <= 1e-4:
        return None
    return Grid(beat_times=beats, source="file")


def derive_file_variants(grid: Grid) -> List[Grid]:
    """Metrical-level variants of a declared grid (double, and both half phases).

    A writer's idea of "one beat" is often an eighth or a half note relative to
    how the music actually reads, and that choice is not recoverable from the
    tempo map alone - so all three reinterpretations get scored.
    """
    bt = grid.beat_times
    out: List[Grid] = []
    if len(bt) >= 4:
        doubled = np.empty(len(bt) * 2 - 1, dtype=float)
        doubled[0::2] = bt
        doubled[1::2] = (bt[:-1] + bt[1:]) / 2.0
        out.append(Grid(doubled, "file:x2"))
    for phase in (0, 1):
        halved = bt[phase::2]
        if len(halved) >= 4:
            out.append(Grid(np.asarray(halved, dtype=float), f"file:half{phase}"))
    return out


def fixed_grid(first_onset: float, last_time: float, bpm: float) -> Grid:
    """Uniform fallback grid anchored on the first onset."""
    ibi = 60.0 / max(bpm, 1.0)
    n = int(math.ceil(max(last_time - first_onset, 0.0) / ibi)) + 4
    beats = first_onset + ibi * np.arange(n, dtype=float)
    return Grid(beats, f"fixed:{int(round(bpm))}")


def score_grid(grid: Grid, clusters: Sequence[Tuple[float, int, float]], cfg: Settings) -> float:
    """Cost of a grid, in seconds: how badly onsets miss its rhythmic positions.

    Alignment error is measured against duple sixteenths, eighth triplets and a
    fine 32nd grid; the last two carry a surcharge so a grid cannot buy accuracy
    by claiming everything is a triplet.
    """
    if not clusters:
        return float("inf")
    duple = (0.0, 0.25, 0.5, 0.75, 1.0)
    triplet = (0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0)
    fine = tuple(k / 8.0 for k in range(9))

    total_w = 0.0
    err_acc = 0.0
    trip_w = 0.0
    fine_w = 0.0
    n_beats = len(grid.beat_times)
    for time, _count, weight in clusters:
        b = grid.to_beats(time)
        if b < -1.0 or b > n_beats + 1.0:
            continue
        index = int(math.floor(b))
        frac = b - index
        ibi = grid.ibi(index)
        err_duple = min(abs(frac - p) for p in duple)
        err_trip = min(abs(frac - p) for p in triplet)
        err_fine = min(abs(frac - p) for p in fine)
        best = min(err_duple, err_trip, err_fine)
        err_acc += weight * min(best * ibi, cfg.err_clip_s)
        if err_trip < err_duple - 1e-9 and err_trip <= err_fine:
            trip_w += weight
        elif err_fine < err_duple - 1e-9 and err_fine < err_trip - 1e-9:
            fine_w += weight
        total_w += weight

    if total_w <= 0.0:
        return float("inf")

    cost = err_acc / total_w
    cost += cfg.triplet_cost_s * (trip_w / total_w)
    cost += cfg.fine_cost_s * (fine_w / total_w)

    bpm = grid.bpm_median()
    over = 0.0
    if bpm < cfg.tempo_soft_min_bpm:
        over = math.log2(cfg.tempo_soft_min_bpm / max(bpm, 1.0))
    elif bpm > cfg.tempo_soft_max_bpm:
        over = math.log2(bpm / cfg.tempo_soft_max_bpm)
    cost += cfg.tempo_penalty_s * over
    return cost


def choose_grid(parsed: ParsedMidi, cfg: Settings) -> Grid:
    """Pick the beat grid: what the file declares, or what the onsets imply."""
    notes = parsed.notes
    clusters = onset_clusters(notes, cfg.onset_cluster_s)
    first_onset = min(n.start for n in notes)
    suspect = parsed.suspect_default_tempo
    tiny = len(clusters) < 8 or (parsed.end_time - first_onset) < 3.0

    file_grid = grid_from_file(parsed)
    candidates: List[Grid] = []
    if file_grid is not None:
        candidates.append(file_grid)
        if not suspect:
            candidates.extend(derive_file_variants(file_grid))

    if tiny:
        chosen = file_grid if (file_grid is not None and not suspect) else fixed_grid(
            first_onset, parsed.end_time, 100.0
        )
        logging.info(
            "Short input (%d onset cluster(s)); using %s grid at %.1f BPM",
            len(clusters),
            chosen.source,
            chosen.bpm_median(),
        )
        return _finalize_grid(chosen, first_onset, parsed.end_time)

    env = build_onset_envelope(notes, parsed.end_time, cfg)
    period = estimate_period_frames(env, cfg)
    if period is not None:
        tracked = track_beats_dp(env, period, cfg)
        if tracked is not None and len(tracked) >= 4:
            candidates.append(Grid(tracked, "estimated"))
    if not candidates:
        candidates.append(fixed_grid(first_onset, parsed.end_time, 100.0))

    scored: List[Tuple[float, Grid, float]] = []
    for cand in candidates:
        raw_cost = score_grid(cand, clusters, cfg)
        adjusted = raw_cost
        if cand.source.startswith("file"):
            adjusted += cfg.grid_margin_s if suspect else -cfg.grid_margin_s
        scored.append((adjusted, cand, raw_cost))
    scored.sort(key=lambda item: item[0])

    best_adj, best, best_raw = scored[0]
    runner_up = scored[1][0] if len(scored) > 1 else float("inf")
    logging.info(
        "Beat grid: %s (%.1f BPM, cost %.1f ms, margin %.1f ms over next best)%s",
        best.source,
        best.bpm_median(),
        best_raw * 1000.0,
        (runner_up - best_adj) * 1000.0 if math.isfinite(runner_up) else 0.0,
        " [file tempo map looks like an unset default]" if suspect else "",
    )
    return _finalize_grid(best, first_onset, parsed.end_time)


def _finalize_grid(grid: Grid, first_onset: float, end_time: float) -> Grid:
    """Extend a winning grid so every note lies inside it.

    The head tolerance is half a beat rather than an epsilon on purpose.  A note
    that sits a few milliseconds before beat one is an anticipation, not evidence
    of an earlier beat, and prepending one would shift every beat index (and so
    every barline) by a full beat.  ``quantize`` clamps such notes to tick zero.
    """
    beats = grid.beat_times
    tolerance = 0.5 * float(beats[1] - beats[0]) if len(beats) >= 2 else 0.0
    return Grid(
        beat_times=_extend_beats(beats, first_onset + tolerance, end_time + 1e-6),
        source=grid.source,
    )


# ---------------------------------------------------------------------------
# Stage 3 - meter and downbeat
# ---------------------------------------------------------------------------

_METER_TEMPLATES: Dict[int, Tuple[float, ...]] = {
    4: (1.0, -0.5, 0.3, -0.8),
    3: (1.0, -0.5, -0.5),
}


def _accent_series(parsed: ParsedMidi, grid: Grid) -> np.ndarray:
    """Per-beat metric accent strength, z-normalised.

    Downbeats in piano music announce themselves with a bass note, a thicker
    chord, a longer note, more force, or by following a rest.  Each contributes.
    """
    n_beats = len(grid.beat_times)
    buckets: List[List[Tuple[int, int, float]]] = [[] for _ in range(n_beats + 1)]
    for note in parsed.notes:
        b = grid.to_beats(note.start)
        idx = int(round(b))
        if idx < 0:
            idx = 0
        if idx >= len(buckets):
            continue
        buckets[idx].append((note.pitch, note.velocity, grid.to_beats(note.end) - b))

    accents = np.zeros(len(buckets), dtype=float)
    for i, items in enumerate(buckets):
        if not items:
            continue
        value = 0.6 * min(len(items), 4) / 4.0
        value += 0.5 * max(v for _p, v, _d in items) / 127.0
        if any(p < 50 for p, _v, _d in items):
            value += 1.0
        if any(d >= 1.8 for _p, _v, d in items):
            value += 0.8
        if i == 0 or not buckets[i - 1]:
            value += 0.4
        accents[i] = value

    std = float(accents.std())
    if std > 1e-9:
        accents = (accents - float(accents.mean())) / std
    return accents


def _best_phase(
    accents: np.ndarray,
    beats_per_bar: int,
    preferred_phase: int = 0,
    bias: float = 0.0,
) -> Tuple[float, int]:
    """Best (score, phase) for one meter template.

    ``preferred_phase`` is the phase that puts the first note on a downbeat, and
    it gets ``bias`` added to its score.  Accent evidence in a transcription is
    weak — a long, loud, low note after a rest reads as a downbeat wherever it
    falls — so without a prior a syncopation talks the detector into a pickup bar
    and shifts every barline in the piece.  Pickups have to earn it.
    """
    template = _METER_TEMPLATES[beats_per_bar]
    preferred = preferred_phase % beats_per_bar
    best_score = -float("inf")
    best_phase = preferred
    for phase in range(beats_per_bar):
        total = 0.0
        for i in range(len(accents)):
            total += accents[i] * template[(i - phase) % beats_per_bar]
        score = total / max(len(accents), 1)
        if phase == preferred:
            score += bias
        if score > best_score:
            best_score = score
            best_phase = phase
    return best_score, best_phase


def detect_meter(
    parsed: ParsedMidi, grid: Grid, cfg: Settings
) -> Tuple[int, int, str]:
    """Choose 4/4 or 3/4 and the beat index of the first downbeat.

    Returns ``(beats_per_bar, first_downbeat_beat_index, provenance)``.  2/4 is
    deliberately not a candidate: at this level of evidence it is
    indistinguishable from 4/4, and guessing it only halves every bar.
    """
    first_onset = min(n.start for n in parsed.notes)
    start_beat = max(int(math.floor(grid.to_beats(first_onset))), 0)

    declared = _declared_meter(parsed, grid, start_beat)
    if declared is not None:
        beats_per_bar, downbeat, why = declared
        logging.info("Meter %d/4 from file time signature (%s)", beats_per_bar, why)
        return beats_per_bar, downbeat, "file"

    accents = _accent_series(parsed, grid)
    score4, phase4 = _best_phase(accents, 4, start_beat, cfg.downbeat_bias)
    score3, phase3 = _best_phase(accents, 3, start_beat, cfg.downbeat_bias)
    if score3 > cfg.meter_bias_34 * score4 + cfg.meter_bias_34_margin:
        beats_per_bar, phase, score = 3, phase3, score3
    else:
        beats_per_bar, phase, score = 4, phase4, score4

    downbeat = start_beat + ((phase - start_beat) % beats_per_bar)
    logging.info(
        "Meter %d/4 (accent score %.3f vs %.3f for the alternative), first downbeat at beat %d",
        beats_per_bar,
        score,
        score4 if beats_per_bar == 3 else score3,
        downbeat,
    )
    return beats_per_bar, downbeat, "estimated"


def _declared_meter(
    parsed: ParsedMidi, grid: Grid, start_beat: int
) -> Optional[Tuple[int, int, str]]:
    """Use the file's time signature only when it carries real information.

    A lone 4/4 at tick 0 is what writers emit by default, so it is ignored; an
    explicit 3/4, or any list of changes, is trusted for its first entry.
    """
    sigs = parsed.time_signatures
    if not sigs:
        return None
    trivial = (
        len(sigs) == 1
        and sigs[0][0] < 1e-6
        and sigs[0][1] == 4
        and sigs[0][2] == 4
    )
    if trivial or grid.source != "file":
        return None

    if len(sigs) > 1:
        logging.warning(
            "File declares %d time signature changes; only the first (%d/%d) is used",
            len(sigs),
            sigs[0][1],
            sigs[0][2],
        )

    _time, num, den = sigs[0]
    if den != 4 or num not in (2, 3, 4):
        logging.warning("Unsupported time signature %d/%d in file; detecting instead", num, den)
        return None
    beats_per_bar = 4 if num == 2 else num

    downbeat = start_beat
    if len(parsed.file_downbeats) > 0:
        candidates = [
            int(round(grid.to_beats(float(t))))
            for t in parsed.file_downbeats
        ]
        candidates = [c for c in candidates if c >= 0]
        if candidates:
            phase = candidates[0] % beats_per_bar
            downbeat = start_beat + ((phase - start_beat) % beats_per_bar)
    return beats_per_bar, downbeat, f"{num}/{den}"


# ---------------------------------------------------------------------------
# Stage 4 - quantization
# ---------------------------------------------------------------------------


def choose_subdivisions(
    parsed: ParsedMidi, grid: Grid, cfg: Settings
) -> Dict[int, int]:
    """Pick a subdivision for every beat independently, then smooth.

    Per-beat choice is what lets a piece contain both straight sixteenths and an
    occasional triplet without notating the whole thing as one or the other.
    """
    n_beats = len(grid.beat_times)
    per_beat: Dict[int, List[Tuple[float, float]]] = {}
    for time, _count, weight in onset_clusters(parsed.notes, cfg.onset_cluster_s):
        b = grid.to_beats(time)
        index = int(math.floor(b))
        frac = b - index
        if frac > 1.0 - 1e-9:
            index += 1
            frac = 0.0
        if index < 0:
            index, frac = 0, 0.0
        per_beat.setdefault(index, []).append((frac, weight))

    costs: Dict[int, Dict[int, float]] = {}
    chosen: Dict[int, int] = {}
    previous = 2
    for b in range(max(n_beats, 1)):
        items = per_beat.get(b)
        if not items:
            chosen[b] = previous
            continue
        ibi = grid.ibi(b)
        beat_costs: Dict[int, float] = {}
        for s in SUBDIVS:
            total_w = 0.0
            acc = 0.0
            collided = 0.0
            taken: set = set()
            for frac, weight in items:
                slot = min(range(s + 1), key=lambda j: abs(frac - j / s))
                err = abs(frac - slot / s)
                acc += weight * min(err * ibi, cfg.subdiv_err_clip_s)
                total_w += weight
                # Two separate attacks landing on one slot is a falsification,
                # not a rounding error, and the error clip alone under-prices it:
                # a third of a beat clips to the same 60 ms as a wild outlier, so
                # without this term subdivision 1 undercuts notating a triplet.
                if slot in taken:
                    collided += weight
                taken.add(slot)
            weight_sum = max(total_w, 1e-9)
            beat_costs[s] = (
                acc / weight_sum
                + SUBDIV_PENALTY[s]
                + cfg.collision_cost_s * collided / weight_sum
            )
        best_s = min(beat_costs, key=lambda s: beat_costs[s])
        costs[b] = beat_costs
        chosen[b] = best_s
        previous = best_s

    _smooth_triplets(chosen, costs, cfg)
    n_trip = sum(1 for s in chosen.values() if s in (3, 6))
    if n_trip:
        logging.info("Quantization: %d of %d beat(s) use triplet subdivisions", n_trip, len(chosen))
    return chosen


def _smooth_triplets(
    chosen: Dict[int, int], costs: Dict[int, Dict[int, float]], cfg: Settings
) -> None:
    """Flip lone triplet beats back to duple when the duple reading is nearly as good.

    An isolated triplet beat between duple neighbours is far more often a timing
    wobble than a real tuplet, and it costs a bracket to notate.
    """
    for b, s in list(chosen.items()):
        if s not in (3, 6) or b not in costs:
            continue
        left = chosen.get(b - 1)
        right = chosen.get(b + 1)
        if (left in (3, 6)) or (right in (3, 6)):
            continue
        duple_costs = {k: v for k, v in costs[b].items() if k in (1, 2, 4, 8)}
        if not duple_costs:
            continue
        best_duple = min(duple_costs, key=lambda k: duple_costs[k])
        if duple_costs[best_duple] <= costs[b][s] + cfg.triplet_flip_margin:
            chosen[b] = best_duple


def quantize(
    parsed: ParsedMidi, grid: Grid, subdiv: Dict[int, int], cfg: Settings
) -> List[QNote]:
    """Snap every note onto the tick grid.

    Onsets use their beat's subdivision.  Offsets use at least a half-beat
    resolution even in beats with no onsets, because a release quantized to a
    whole beat turns every held chord into a bar-long smear.
    """
    unit = lambda s: DIVS // s  # noqa: E731 - tiny local helper
    out: List[QNote] = []
    for note in parsed.notes:
        on_b = grid.to_beats(note.start)
        on_index = max(int(math.floor(on_b)), 0)
        s_on = subdiv.get(on_index, 2)
        j = int(round((on_b - on_index) * s_on))
        if j >= s_on:
            on_index += 1
            s_on = subdiv.get(on_index, s_on)
            j = 0
        on_tick = DIVS * on_index + unit(s_on) * j

        off_b = grid.to_beats(note.end)
        off_index = max(int(math.floor(off_b)), 0)
        s_off = max(subdiv.get(off_index, 2), 2)
        k = int(round((off_b - off_index) * s_off))
        if k >= s_off:
            off_index += 1
            s_off = max(subdiv.get(off_index, s_off), 2)
            k = 0
        off_tick = DIVS * off_index + unit(s_off) * k

        if off_tick <= on_tick:
            off_tick = on_tick + unit(max(s_on, 2))
        out.append(QNote(on=on_tick, off=off_tick, pitch=note.pitch, velocity=note.velocity))

    out.sort(key=lambda q: (q.on, q.pitch))
    return out


def clean_quantized(qnotes: List[QNote], cfg: Settings) -> List[QNote]:
    """Remove duplicates and same-pitch overlaps introduced by snapping."""
    merged: Dict[Tuple[int, int], QNote] = {}
    order: List[Tuple[int, int]] = []
    for q in qnotes:
        key = (q.on, q.pitch)
        prev = merged.get(key)
        if prev is None:
            merged[key] = q
            order.append(key)
        else:
            if q.velocity > prev.velocity:
                prev.velocity = q.velocity
            prev.off = max(prev.off, q.off)
    out = [merged[k] for k in order]
    out.sort(key=lambda q: (q.on, q.pitch))

    last: Dict[int, QNote] = {}
    for q in out:
        prev = last.get(q.pitch)
        if prev is not None and prev.off > q.on:
            prev.off = q.on
        last[q.pitch] = q
    out = [q for q in out if q.off > q.on]
    if not out:
        raise ValueError("MIDI file contains no notes after quantization")
    return out


# ---------------------------------------------------------------------------
# Stage 5 - hands / staves
# ---------------------------------------------------------------------------


def _group_by_onset(qnotes: Sequence[QNote]) -> List[List[QNote]]:
    groups: List[List[QNote]] = []
    current: List[QNote] = []
    for q in sorted(qnotes, key=lambda n: (n.on, n.pitch)):
        if current and q.on != current[0].on:
            groups.append(current)
            current = []
        current.append(q)
    if current:
        groups.append(current)
    return groups


def _diatonic(pitch: int) -> int:
    """Diatonic index of a MIDI pitch, spelled naturally.

    This runs before the key is known, so it cannot ask for the real spelling.
    Naturals are exact and accidentals land within one index of the truth, which
    moves a ledger count by at most one - fine for weighing one staff against the
    other, and not worth reordering the pipeline for.
    """
    return (pitch // 12 - 1) * 7 + _PC_DIATONIC[pitch % 12]


def _ledger_lines(diatonic: int, staff: int) -> int:
    """How many ledger lines a notehead needs to be read on this staff."""
    low, high = STAFF_EXTENT[staff]
    if diatonic < low:
        return (low - diatonic) // 2
    if diatonic > high:
        return (diatonic - high) // 2
    return 0


def _hand_cut_cost(pitches: Sequence[int], cut: int, cfg: Settings) -> float:
    """Cost of reading ``pitches[:cut]`` on the bass staff and the rest on treble."""
    cost = 0.0
    for half, staff in ((pitches[:cut], 2), (pitches[cut:], 1)):
        if not half:
            continue
        cost += sum(_ledger_lines(_diatonic(p), staff) for p in half)
        excess = (half[-1] - half[0]) - cfg.hand_span_semitones
        if excess > 0:
            cost += cfg.hand_span_penalty * excess
    return cost


def assign_hands(qnotes: List[QNote], cfg: Settings) -> None:
    """Assign every note to staff 1 (right hand) or staff 2 (left hand), in place.

    The thing that makes a grand staff readable is that few notes need ledger
    lines, so that is what this minimises directly.  Each simultaneity is divided
    at a single pitch - everything below it to the left hand, everything above to
    the right - because hands do not interleave, which leaves only as many choices
    per chord as it has distinct pitches.  A Viterbi pass picks the divisions for
    the whole piece at once, so a chord is read in the light of its neighbours
    rather than on its own.

    Choosing per chord in isolation is what the old largest-gap rule did, and it
    failed on the commonest left-hand texture there is: a doubled octave is a
    12-semitone gap, so it read as the gap between the hands and sent the upper
    note to the treble staff, seven ledger lines below the staff it was drawn on.
    """
    groups = _group_by_onset(qnotes)
    if not groups:
        logging.info("Staff split: nothing to assign")
        return

    # Viterbi.  A state is a cut index: how many of this chord's pitches, counting
    # up from the bottom, the left hand takes.
    best_cost: List[float] = []
    best_prev: List[List[int]] = []
    prev_centres: List[Tuple[Optional[float], Optional[float]]] = []

    for group in groups:
        pitches = sorted({q.pitch for q in group})
        centres: List[Tuple[Optional[float], Optional[float]]] = []
        for cut in range(len(pitches) + 1):
            low, high = pitches[:cut], pitches[cut:]
            centres.append(
                (
                    sum(low) / len(low) if low else None,
                    sum(high) / len(high) if high else None,
                )
            )

        costs = [_hand_cut_cost(pitches, cut, cfg) for cut in range(len(pitches) + 1)]
        if not best_cost:
            best_cost, best_prev = costs, [[-1] * len(costs)]
            prev_centres = centres
            continue

        chosen: List[int] = []
        for cut, (left_c, right_c) in enumerate(centres):
            cheapest = math.inf
            argmin = 0
            for prev_cut, prior in enumerate(best_cost):
                prev_left, prev_right = prev_centres[prev_cut]
                move = 0.0
                if left_c is not None and prev_left is not None:
                    move += abs(left_c - prev_left)
                if right_c is not None and prev_right is not None:
                    move += abs(right_c - prev_right)
                total = prior + cfg.hand_move_penalty * move
                if total < cheapest:
                    cheapest, argmin = total, prev_cut
            costs[cut] += cheapest
            chosen.append(argmin)
        best_cost, prev_centres = costs, centres
        best_prev.append(chosen)

    # Walk the choices back, cheapest end first.
    cuts: List[int] = [0] * len(groups)
    cut = min(range(len(best_cost)), key=lambda i: best_cost[i])
    for index in range(len(groups) - 1, -1, -1):
        cuts[index] = cut
        cut = best_prev[index][cut]
        if cut < 0:
            break

    for group, cut in zip(groups, cuts):
        to_left = set(sorted({q.pitch for q in group})[:cut])
        for q in group:
            q.staff = 2 if q.pitch in to_left else 1

    n_left = sum(1 for q in qnotes if q.staff == 2)
    ledger = sum(_ledger_lines(_diatonic(q.pitch), q.staff) for q in qnotes)
    logging.info(
        "Staff split: %d note(s) right hand, %d note(s) left hand, "
        "%.2f ledger line(s) per note",
        len(qnotes) - n_left,
        n_left,
        ledger / len(qnotes),
    )


def legato_fill(qnotes: List[QNote], cfg: Settings) -> None:
    """Close tiny gaps between a release and the next attack on the same staff.

    Transcription models release a hair early; without this every bar picks up a
    scatter of 32nd rests that mean nothing musically.
    """
    for staff in (1, 2):
        staff_notes = [q for q in qnotes if q.staff == staff]
        onsets = sorted({q.on for q in staff_notes})
        if not onsets:
            continue
        filled = 0
        for q in staff_notes:
            i = int(np.searchsorted(np.asarray(onsets), q.off, side="left"))
            if i >= len(onsets):
                continue
            gap = onsets[i] - q.off
            if 0 < gap <= cfg.legato_fill_ticks:
                q.off = onsets[i]
                filled += 1
        if filled:
            logging.info("Legato-filled %d gap(s) on staff %d", filled, staff)


# ---------------------------------------------------------------------------
# Stage 6 - voice separation
# ---------------------------------------------------------------------------


def _partition_layers(members: List[QNote], cfg: Settings) -> List[List[QNote]]:
    """Split one simultaneity into a sustained layer and a moving layer, if any.

    A held bass note under a run of sixteenths is two voices, not a chord; the
    duration spread is the signal.
    """
    if len(members) < 2:
        return [members]
    durs = [m.dur for m in members]
    if max(durs) < 2 * min(durs) or max(durs) < DIVS:
        return [members]
    threshold = (max(durs) + min(durs)) / 2.0
    long_layer = [m for m in members if m.dur >= threshold]
    short_layer = [m for m in members if m.dur < threshold]
    if not long_layer or not short_layer:
        return [members]
    layers = [long_layer, short_layer]
    layers.sort(key=lambda layer: max(m.pitch for m in layer), reverse=True)
    return layers


def _as_event(layer: Sequence[QNote]) -> VoiceEvent:
    pitches = tuple(sorted({m.pitch for m in layer}))
    return VoiceEvent(
        on=layer[0].on,
        dur=max(m.dur for m in layer),
        kind="note",
        pitches=pitches,
        velocity=max(m.velocity for m in layer),
    )


def separate_voices(
    staff_notes: Sequence[QNote], cfg: Settings
) -> Tuple[List[VoiceEvent], List[VoiceEvent]]:
    """Distribute one staff's notes over at most two voices.

    Notes keep their full length; conflicts are settled when the next attack
    arrives - a short overlap is trimmed, a held note under a new higher entry is
    demoted to the lower voice, and anything else is routed to the free voice.
    That ordering is what keeps sustained notes intact instead of chopping every
    one of them at the next onset.
    """
    voices: List[List[VoiceEvent]] = [[], []]

    def free_at(v: int) -> int:
        return voices[v][-1].off if voices[v] else -1

    def top_pitch(event: VoiceEvent) -> int:
        return max(event.pitches) if event.pitches else -1

    for group in _group_by_onset(staff_notes):
        layers = _partition_layers(list(group), cfg)
        for order, layer in enumerate(layers):
            event = _as_event(layer)
            want = 0 if order == 0 else 1
            placed = False
            for v in (want, 1 - want):
                if free_at(v) <= event.on:
                    voices[v].append(event)
                    placed = True
                    break
            if placed:
                continue

            # Both voices are still sounding at this onset.
            candidates = sorted((0, 1), key=lambda v: (voices[v][-1].on, v))
            trimmed = False
            for v in (want, 1 - want):
                held = voices[v][-1]
                overlap = held.off - event.on
                if overlap <= cfg.trunc_max_ticks and overlap <= cfg.trunc_max_frac * held.dur:
                    held.dur = event.on - held.on
                    voices[v].append(event)
                    trimmed = True
                    break
            if trimmed:
                continue

            held_upper = voices[0][-1]
            other_free = free_at(1) <= held_upper.on
            if top_pitch(event) > top_pitch(held_upper) and other_free:
                voices[0].pop()
                voices[1].append(held_upper)
                voices[0].append(event)
                continue

            # Last resort: the least-recent held note yields its voice.
            victim_voice = candidates[0]
            victim = voices[victim_voice][-1]
            victim.dur = event.on - victim.on
            voices[victim_voice].append(event)

    for stream in voices:
        for i in range(len(stream) - 1):
            if stream[i].off > stream[i + 1].on:
                stream[i].dur = stream[i + 1].on - stream[i].on
        stream[:] = [e for e in stream if e.dur > 0]

    upper, lower = voices
    if not lower:
        return upper, []
    return upper, lower


# ---------------------------------------------------------------------------
# Stage 7 - key detection and spelling
# ---------------------------------------------------------------------------


def _pearson(a: Sequence[float], b: Sequence[float]) -> float:
    va = np.asarray(a, dtype=float)
    vb = np.asarray(b, dtype=float)
    va = va - va.mean()
    vb = vb - vb.mean()
    denom = float(np.sqrt((va * va).sum() * (vb * vb).sum()))
    if denom < 1e-12:
        return 0.0
    return float((va * vb).sum() / denom)


def key_fifths(tonic_pc: int, is_major: bool) -> int:
    """Signed number of sharps (positive) or flats (negative) for a key."""
    reference = tonic_pc if is_major else (tonic_pc + 3) % 12
    fifths = (reference * 7) % 12
    if fifths > 6:
        fifths -= 12
    return fifths


def detect_key(qnotes: Sequence[QNote]) -> Tuple[int, bool, int]:
    """Krumhansl-Schmuckler key finding over a duration+velocity weighted histogram.

    Returns ``(tonic_pitch_class, is_major, fifths)``.  Weighting by duration
    matters: a long tonic pedal says more about the key than a fast passing note.
    """
    histogram = np.zeros(12, dtype=float)
    for q in qnotes:
        weight = (q.dur / DIVS) * (0.5 + 0.5 * (q.velocity / 127.0))
        histogram[q.pitch % 12] += weight
    if histogram.sum() <= 0:
        return 0, True, 0

    best: Optional[Tuple[float, int, bool, int]] = None
    for tonic in range(12):
        rotated = [histogram[(tonic + i) % 12] for i in range(12)]
        for is_major, profile in ((True, KS_MAJOR), (False, KS_MINOR)):
            score = _pearson(rotated, profile)
            fifths = key_fifths(tonic, is_major)
            # Ties break toward major, then toward the simpler key signature.
            rank = (-score, 0 if is_major else 1, abs(fifths))
            if best is None or rank < (-best[0], 0 if best[2] else 1, abs(best[3])):
                best = (score, tonic, is_major, fifths)

    assert best is not None
    score, tonic, is_major, fifths = best
    logging.info(
        "Key: %s %s (%+d, correlation %.3f)",
        key_name(fifths, is_major),
        "major" if is_major else "minor",
        fifths,
        score,
    )
    return tonic, is_major, fifths


def key_name(fifths: int, is_major: bool) -> str:
    """Name a key the way its own signature spells it.

    Deriving the name from the line of fifths rather than from a pitch-class
    table is what keeps the name and the signature agreeing: five flats is Db
    major, and naming that pitch class "C#" would describe a key of seven sharps.
    """
    index = fifths if is_major else fifths + 3
    letter = "FCGDAEB"[(index + 1) % 7]
    alter = (index + 1) // 7
    return letter + ("#" * alter if alter > 0 else "b" * -alter)


def _lof(step: str, alter: int) -> int:
    return LOF_BASE[step] + 7 * alter


def build_spelling(tonic_pc: int, is_major: bool, fifths: int) -> Dict[int, Tuple[str, int]]:
    """Choose one spelling per pitch class, by proximity on the line of fifths.

    Centring the window two fifths sharp of the key signature is what makes F#
    major spell its notes with sharps and Eb major spell them with flats, instead
    of every accidental defaulting to one direction.  Minor keys additionally get
    a raised leading tone, since that is how minor is actually written.
    """
    center = fifths + 2
    table: Dict[int, Tuple[str, int]] = {}
    for pc in range(12):
        candidates = [
            (step, alter)
            for step, alter in SPELLINGS
            if (STEP_PC[step] + alter) % 12 == pc
        ]
        candidates.sort(
            key=lambda sa: (
                abs(_lof(sa[0], sa[1]) - center),
                abs(sa[1]),
                -sa[1],
            )
        )
        table[pc] = candidates[0]

    if not is_major:
        leading_pc = (tonic_pc - 1) % 12
        target = fifths + 8
        for step, alter in SPELLINGS:
            if (STEP_PC[step] + alter) % 12 == leading_pc and _lof(step, alter) == target:
                table[leading_pc] = (step, alter)
                break
    return table


def spell_pitch(midi: int, table: Dict[int, Tuple[str, int]]) -> Tuple[str, int, int]:
    """MIDI number -> (step, alter, octave), exact for B#/Cb style wraparound."""
    step, alter = table[midi % 12]
    octave = (midi - STEP_PC[step] - alter) // 12 - 1
    return step, alter, octave


# ---------------------------------------------------------------------------
# Stage 8 - measures, tuplet groups and duration decomposition
# ---------------------------------------------------------------------------


def plan_measures(
    first_tick: int,
    last_tick: int,
    beats_per_bar: int,
    downbeat_tick: int,
    cfg: Settings,
) -> List[MeasureCtx]:
    """Lay out the bar grid, with a pickup measure when the music starts mid-bar."""
    bar_len = beats_per_bar * DIVS
    origin = min((first_tick // DIVS) * DIVS, downbeat_tick)
    pickup_len = downbeat_tick - origin

    measures: List[MeasureCtx] = []
    if pickup_len > 0:
        measures.append(
            MeasureCtx(
                number=0,
                start=origin,
                length=pickup_len,
                implicit=True,
                beats=beats_per_bar,
            )
        )
        logging.info("Pickup measure of %d tick(s) (%g beat(s))", pickup_len, pickup_len / DIVS)

    cursor = downbeat_tick
    number = 1
    while cursor < last_tick or number == 1:
        measures.append(
            MeasureCtx(number=number, start=cursor, length=bar_len, beats=beats_per_bar)
        )
        cursor += bar_len
        number += 1
        if number > cfg.max_measures:
            raise ValueError(
                f"Score would exceed the {cfg.max_measures}-measure safety cap; "
                "the beat grid is probably wrong"
            )
    logging.info(
        "Score layout: %d measure(s) of %d/4%s",
        len(measures),
        beats_per_bar,
        " plus pickup" if pickup_len > 0 else "",
    )
    return measures


def metric_strength(tick: int, ctx: MeasureCtx) -> int:
    """Metric weight of an absolute tick, expressed as the level that divides it.

    A pickup measure is measured as if right-aligned inside a full bar, which is
    what makes its notes get the beaming and grouping of the bar they lead into.
    """
    rel = tick - ctx.start
    if ctx.implicit:
        rel += ctx.beats * DIVS - ctx.length
    levels = METRIC_LEVELS[ctx.beats]
    for level in levels:
        if rel % level == 0:
            return level
    return levels[-1]


def _admissible(tick: int, dur: int, is_rest: bool, ctx: MeasureCtx) -> bool:
    """May a single symbol of this duration start here?

    The rules are the classic engraving ones: an undotted value may straddle a
    weaker boundary (that is how syncopation is written), a dotted value needs its
    undotted base to fit the position, and a rest must sit on a boundary of its
    own size so the bar stays readable.
    """
    display = DUPLE_DISPLAY.get(dur)
    if display is None:
        return False
    _type, dots = display
    strength = metric_strength(tick, ctx)
    if is_rest:
        return dots == 0 and strength >= dur
    if dots == 1:
        return 3 * strength >= 2 * dur
    return 2 * strength >= dur


def decompose_duple(tick: int, dur: int, is_rest: bool, ctx: MeasureCtx) -> List[Tuple[int, int]]:
    """Break a span into notatable duple durations, splitting at strong positions."""
    if dur <= 0:
        return []
    if _admissible(tick, dur, is_rest, ctx):
        return [(tick, dur)]

    offset = ctx.beats * DIVS - ctx.length if ctx.implicit else 0
    rel_start = tick - ctx.start + offset
    rel_end = rel_start + dur
    for level in METRIC_LEVELS[ctx.beats]:
        low = ((rel_start // level) + 1) * level
        candidates = list(range(low, rel_end, level))
        if not candidates:
            continue
        midpoint = (rel_start + rel_end) / 2.0
        candidates.sort(key=lambda x: (abs(x - midpoint), x))
        split_rel = candidates[0]
        split = split_rel - offset + ctx.start
        left = decompose_duple(tick, split - tick, is_rest, ctx)
        right = decompose_duple(split, tick + dur - split, is_rest, ctx)
        return left + right

    logging.warning("Could not decompose %d tick(s) at tick %d; emitting as is", dur, tick)
    return [(tick, dur)]


def _beat_subdiv(tick: int, subdiv: Dict[int, int]) -> int:
    return subdiv.get(tick // DIVS, 2)


def tuplet_group_bounds(tick: int, subdiv: Dict[int, int]) -> Optional[Tuple[int, int, int]]:
    """The tuplet group containing ``tick``, as ``(start, end, subdivision)``.

    One 3:2 group per beat for eighth triplets; two per beat for sixteenth
    triplets, so a sextuplet is written as what it is - two triplets - rather than
    one six-note bracket that no engraver would draw.
    """
    beat = tick // DIVS
    s = subdiv.get(beat, 2)
    if s not in (3, 6):
        return None
    beat_start = beat * DIVS
    if s == 3:
        return beat_start, beat_start + DIVS, 3
    half = DIVS // 2
    if tick - beat_start < half:
        return beat_start, beat_start + half, 6
    return beat_start + half, beat_start + DIVS, 6


def _split_points(tick: int, dur: int, subdiv: Dict[int, int]) -> List[int]:
    """Beat and tuplet-group boundaries strictly inside a span."""
    points = set()
    end = tick + dur
    first_beat = tick // DIVS
    last_beat = (end - 1) // DIVS
    for beat in range(first_beat, last_beat + 1):
        boundaries = [beat * DIVS]
        if subdiv.get(beat, 2) == 6:
            boundaries.append(beat * DIVS + DIVS // 2)
        boundaries.append((beat + 1) * DIVS)
        for b in boundaries:
            if tick < b < end:
                points.add(b)
    return sorted(points)


def _is_duple_tick(tick: int) -> bool:
    return tick % 60 == 0


def _measure_index(measures: Sequence[MeasureCtx], tick: int) -> int:
    starts = [m.start for m in measures]
    i = int(np.searchsorted(np.asarray(starts), tick, side="right")) - 1
    return min(max(i, 0), len(measures) - 1)


def split_at_barlines(
    events: Sequence[VoiceEvent], measures: Sequence[MeasureCtx]
) -> Dict[int, List[Fragment]]:
    """Cut every event at barlines, marking the joints as ties.

    Nothing may cross a barline in notation, so a held chord becomes one chord per
    bar joined by ties - which is exactly what the old converter got wrong by
    simply clipping.
    """
    out: Dict[int, List[Fragment]] = {}
    for event in events:
        start = event.on
        end = event.off
        index = _measure_index(measures, start)
        while start < end and index < len(measures):
            ctx = measures[index]
            seg_end = min(end, ctx.start + ctx.length)
            if seg_end <= start:
                index += 1
                continue
            out.setdefault(index, []).append(
                Fragment(
                    on=start,
                    dur=seg_end - start,
                    kind=event.kind,
                    pitches=event.pitches,
                    velocity=event.velocity,
                    tie_in=start > event.on,
                    tie_out=seg_end < end,
                )
            )
            start = seg_end
            index += 1
    return out


def fill_rests(pieces: List[Fragment], ctx: MeasureCtx) -> List[Fragment]:
    """Pad a measure's worth of one voice with rests so it sums to the bar length."""
    pieces = sorted(pieces, key=lambda f: f.on)
    out: List[Fragment] = []
    cursor = ctx.start
    limit = ctx.start + ctx.length
    for piece in pieces:
        if piece.on < cursor:
            overlap = cursor - piece.on
            if overlap >= piece.dur:
                continue
            piece.on = cursor
            piece.dur -= overlap
            piece.tie_in = True
        if piece.on > cursor:
            out.append(Fragment(on=cursor, dur=piece.on - cursor, kind="rest"))
        if piece.on + piece.dur > limit:
            piece.dur = limit - piece.on
            piece.tie_out = False
        if piece.dur <= 0:
            continue
        out.append(piece)
        cursor = piece.on + piece.dur
    if cursor < limit:
        out.append(Fragment(on=cursor, dur=limit - cursor, kind="rest"))
    return out


def _fallback_display(dur: int) -> Tuple[str, int]:
    """Last-resort note type for a duration no table covers."""
    best = min(DUPLE_DISPLAY, key=lambda d: (abs(d - dur), d))
    logging.warning("No display type for duration %d; using %s", dur, DUPLE_DISPLAY[best][0])
    return DUPLE_DISPLAY[best]


def _tuplet_units(a: int, b: int, unit: int) -> List[Tuple[int, int]]:
    spans: List[Tuple[int, int]] = []
    cursor = a
    while cursor < b:
        step = min(unit, b - cursor)
        spans.append((cursor, step))
        cursor += step
    return spans


def decompose_fragment(
    piece: Fragment, ctx: MeasureCtx, subdiv: Dict[int, int]
) -> List[Fragment]:
    """Turn one span into the sequence of symbols that actually notates it."""
    is_rest = piece.kind == "rest"
    specs: List[Tuple[int, int, Optional[Tuple[int, int]]]] = []

    if _is_duple_tick(piece.on) and _is_duple_tick(piece.off):
        specs = [(p, d, None) for p, d in decompose_duple(piece.on, piece.dur, is_rest, ctx)]
    else:
        cuts = [piece.on, *_split_points(piece.on, piece.dur, subdiv), piece.off]
        for a, b in zip(cuts, cuts[1:]):
            if b <= a:
                continue
            group = tuplet_group_bounds(a, subdiv)
            full_span = group is not None and a == group[0] and b == group[1]
            duple_ends = _is_duple_tick(a) and _is_duple_tick(b)
            if group is None or full_span or duple_ends:
                specs.extend((p, d, None) for p, d in decompose_duple(a, b - a, is_rest, ctx))
                continue
            s = group[2]
            if (b - a) in TUPLET_DISPLAY[s]:
                specs.append((a, b - a, (3, 2)))
            else:
                for p, d in _tuplet_units(a, b, DIVS // s):
                    specs.append((p, d, (3, 2)))

    frags: List[Fragment] = []
    last = len(specs) - 1
    for i, (p, d, tmod) in enumerate(specs):
        display: Optional[Tuple[str, int]] = None
        if tmod is not None:
            group = tuplet_group_bounds(p, subdiv)
            if group is not None:
                display = TUPLET_DISPLAY[group[2]].get(d)
        else:
            display = DUPLE_DISPLAY.get(d)
        note_type, dots = display if display is not None else _fallback_display(d)
        frags.append(
            Fragment(
                on=p,
                dur=d,
                kind=piece.kind,
                pitches=piece.pitches,
                velocity=piece.velocity,
                tie_in=piece.tie_in if i == 0 else (not is_rest),
                tie_out=piece.tie_out if i == last else (not is_rest),
                disp_type=note_type,
                dots=dots,
                tmod=tmod,
            )
        )
    return frags


def assign_tuplet_marks(frags: Sequence[Fragment], subdiv: Dict[int, int]) -> None:
    """Bracket each contiguous run of tuplet members inside one group."""
    run: List[Fragment] = []
    run_key: Optional[Tuple[int, int]] = None

    def close(run_frags: List[Fragment]) -> None:
        if not run_frags:
            return
        if len(run_frags) == 1:
            run_frags[0].tuplet_mark = "both"
        else:
            run_frags[0].tuplet_mark = "start"
            run_frags[-1].tuplet_mark = "stop"

    for frag in frags:
        if frag.tmod is None:
            close(run)
            run, run_key = [], None
            continue
        group = tuplet_group_bounds(frag.on, subdiv)
        key = (group[0], group[1]) if group is not None else None
        if key != run_key:
            close(run)
            run, run_key = [], key
        run.append(frag)
    close(run)


def assemble_measures(
    voice_streams: Dict[int, List[VoiceEvent]],
    measures: Sequence[MeasureCtx],
    subdiv: Dict[int, int],
) -> List[Dict[int, List[Fragment]]]:
    """Build, for every measure, the notated fragments of every voice present."""
    result: List[Dict[int, List[Fragment]]] = [{} for _ in measures]
    for voice, events in voice_streams.items():
        if not events:
            continue
        per_measure = split_at_barlines(events, measures)
        for index, pieces in per_measure.items():
            ctx = measures[index]
            frags: List[Fragment] = []
            for piece in fill_rests(pieces, ctx):
                frags.extend(decompose_fragment(piece, ctx, subdiv))
            assign_tuplet_marks(frags, subdiv)
            assign_beams(frags, subdiv)
            hide_padding_rests(frags, voice)
            result[index][voice] = frags
    return result


def hide_padding_rests(frags: List[Fragment], voice: int) -> None:
    """Hide the rests that only pad a secondary voice out to the bar length.

    Every voice has to sum to the measure length, so a second voice holding one
    late note still needs the earlier beats filled.  Printing those rests is
    what makes machine transcriptions look like rest soup: a reader sees a bar of
    rests under the melody and looks for a part that is not there.  Engravers
    hide leading and trailing padding in secondary voices and keep the interior
    rests, which do carry meaning — they are silence *between* that voice's own
    notes.  Voices 1 and 5 are the staff's primary voice and keep every rest.
    """
    if voice not in (2, 6):
        return
    note_positions = [i for i, f in enumerate(frags) if f.kind == "note"]
    if not note_positions:
        # Nothing but padding: the voice is not emitted at all in this measure.
        return
    first, last = note_positions[0], note_positions[-1]
    for i, frag in enumerate(frags):
        if frag.kind == "rest" and (i < first or i > last):
            frag.invisible = True


# ---------------------------------------------------------------------------
# Stage 9 - beaming
# ---------------------------------------------------------------------------


def _beam_unit(tick: int, subdiv: Dict[int, int]) -> Tuple[int, int]:
    """Which beam group a tick belongs to: one per beat, or per half beat in sextuplets."""
    beat = tick // DIVS
    if subdiv.get(beat, 2) == 6:
        return beat, 0 if (tick - beat * DIVS) < DIVS // 2 else 1
    return beat, 0


def assign_beams(frags: Sequence[Fragment], subdiv: Dict[int, int]) -> None:
    """Beam notes together within a beat, in place.

    Beams are the main visual cue for where the beat is, so they are grouped per
    beat and broken by rests and by anything a quarter note or longer.
    """
    runs: List[List[Fragment]] = []
    current: List[Fragment] = []
    unit: Optional[Tuple[int, int]] = None
    for frag in frags:
        beamable = frag.kind == "note" and frag.disp_type in _BEAM_TYPES
        frag_unit = _beam_unit(frag.on, subdiv) if beamable else None
        if not beamable or frag_unit != unit:
            if len(current) > 1:
                runs.append(current)
            current = []
            unit = frag_unit
        if beamable:
            current.append(frag)
    if len(current) > 1:
        runs.append(current)

    for run in runs:
        levels = [_BEAM_TYPES[f.disp_type] for f in run]  # type: ignore[index]
        for level in range(1, max(levels) + 1):
            i = 0
            while i < len(run):
                if levels[i] < level:
                    i += 1
                    continue
                j = i
                while j + 1 < len(run) and levels[j + 1] >= level:
                    j += 1
                if i == j:
                    # A lone note at this level gets a partial beam pointing at
                    # the neighbour it belongs to rhythmically.
                    run[i].beams[level] = "backward hook" if i > 0 else "forward hook"
                else:
                    run[i].beams[level] = "begin"
                    for k in range(i + 1, j):
                        run[k].beams[level] = "continue"
                    run[j].beams[level] = "end"
                i = j + 1


# ---------------------------------------------------------------------------
# Stage 10 - directions
# ---------------------------------------------------------------------------


def _dynamic_band(velocity: float) -> int:
    for index, (limit, _name) in enumerate(DYNAMIC_THRESHOLDS):
        if velocity <= limit:
            return index
    return len(DYNAMIC_THRESHOLDS) - 1


def compute_dynamics(qnotes: Sequence[QNote], cfg: Settings) -> List[Tuple[int, str]]:
    """Derive dynamic marks from smoothed velocity.

    Hysteresis on both the level and the spacing is essential: raw transcription
    velocities wobble by a band or two from note to note, and a score covered in
    alternating mf/f marks is worse than no marks at all.
    """
    notes = sorted(qnotes, key=lambda q: q.on)
    if not notes:
        return []

    ema = float(notes[0].velocity)
    marks: List[Tuple[int, str]] = []
    band = _dynamic_band(ema)
    marks.append((notes[0].on, DYNAMIC_THRESHOLDS[band][1]))
    last_tick = notes[0].on

    for q in notes[1:]:
        ema = (1.0 - cfg.dyn_ema) * ema + cfg.dyn_ema * q.velocity
        candidate = _dynamic_band(ema)
        if candidate == band:
            continue
        if (q.on - last_tick) < cfg.dyn_min_gap_beats * DIVS:
            continue
        if candidate > band:
            boundary = DYNAMIC_THRESHOLDS[band][0]
            if ema < boundary + cfg.dyn_margin:
                continue
        else:
            boundary = DYNAMIC_THRESHOLDS[band - 1][0] if band > 0 else 0
            if ema > boundary - cfg.dyn_margin:
                continue
        band = candidate
        marks.append((q.on, DYNAMIC_THRESHOLDS[band][1]))
        last_tick = q.on

    logging.info("Dynamics: %d mark(s) (%s)", len(marks), ", ".join(m for _t, m in marks[:8]))
    return marks


def quantize_pedal(
    parsed: ParsedMidi,
    grid: Grid,
    anchors: Sequence[int],
    first_tick: int,
    last_tick: int,
    cfg: Settings,
) -> List[Tuple[int, int]]:
    """Turn CC64 into clean pedal spans, in ticks.

    Real pedalling produces a stream of chattering controller values; without
    debouncing this becomes dozens of unreadable one-note pedal marks.

    `anchors` are the notated positions a mark may be placed at - the onsets of
    the voice that carries the pedal line.  `first_tick` and `last_tick` bound
    the notated range, which does not generally start at zero: a pickup pushes
    the first barline later.
    """
    if not parsed.pedal or not anchors:
        return []

    spans: List[Tuple[float, float]] = []
    down_at: Optional[float] = None
    for time, value in parsed.pedal:
        if value >= cfg.pedal_on_value:
            if down_at is None:
                down_at = time
        else:
            if down_at is not None:
                spans.append((down_at, time))
                down_at = None
    if down_at is not None:
        spans.append((down_at, parsed.end_time))

    merged: List[List[float]] = []
    for start, end in spans:
        if merged and start - merged[-1][1] < cfg.pedal_merge_s:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    kept = [(s, e) for s, e in merged if (e - s) >= cfg.pedal_min_s]

    positions = np.asarray(sorted(set(anchors)), dtype=np.int64)

    def snap(seconds: float) -> int:
        tick = grid.to_beats(seconds) * DIVS
        # Held into the notated range.  Pedalling that happens before the first
        # barline has nowhere of its own to be written, and a mark outside every
        # measure gets filed into measure 1 anyway - where it stacks up against
        # the marks that legitimately live there and inverts their order.
        tick = min(max(tick, float(first_tick)), float(last_tick))
        # Then onto a notated position.  A pedal mark can only be drawn at a note,
        # so a mark left sitting between two onsets gets pulled to one of them by
        # the renderer - and when two marks share the gap they land on the same
        # note in the wrong order, which is how a bracket loses its start.
        i = int(np.searchsorted(positions, tick))
        if i == 0:
            return int(positions[0])
        if i >= len(positions):
            return int(positions[-1])
        lo, hi = int(positions[i - 1]), int(positions[i])
        return lo if (tick - lo) <= (hi - tick) else hi

    def next_position(tick: int) -> Optional[int]:
        i = int(np.searchsorted(positions, tick, side="right"))
        return int(positions[i]) if i < len(positions) else None

    out: List[Tuple[int, int]] = []
    for start, end in kept:
        a = snap(start)
        b = snap(end)
        if b <= a:
            # Briefer than the gap between two notated positions.  Let it reach
            # the next one rather than dropping it: a bracket needs some extent.
            following = next_position(a)
            if following is None:
                continue
            b = following
        # The debouncing above measures in seconds, so it cannot see two spans
        # land on one notated position.  Notation has no way to say "lift and
        # press again here", so join them: left alone, the renderer meets a stop
        # and a start at the same moment and drops one of the two brackets.
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
            continue
        out.append((a, b))
    logging.info(
        "Pedal: %d span(s) from %d CC64 event(s)", len(out), len(parsed.pedal)
    )
    return out


def pick_tempo_bpm(grid: Grid) -> int:
    """One representative tempo for the whole score.

    Per-beat tempo maps encode rubato, not tempo changes; writing them out as
    directions would fabricate an accelerando in every bar.
    """
    return max(int(round(grid.bpm_median())), 20)


# ---------------------------------------------------------------------------
# Stage 11 - MusicXML emission
# ---------------------------------------------------------------------------

_SHARP_ORDER = "FCGDAEB"
_FLAT_ORDER = "BEADGCF"
ACCIDENTAL_NAMES: Dict[int, str] = {
    -2: "flat-flat",
    -1: "flat",
    0: "natural",
    1: "sharp",
    2: "sharp-sharp",
}


def key_signature_alters(fifths: int) -> Dict[str, int]:
    """Which steps the key signature already alters."""
    out: Dict[str, int] = {}
    if fifths > 0:
        for i in range(min(fifths, 7)):
            out[_SHARP_ORDER[i]] = 1
    elif fifths < 0:
        for i in range(min(-fifths, 7)):
            out[_FLAT_ORDER[i]] = -1
    return out


class AccidentalState:
    """Tracks which accidentals are already in force, per (step, octave), per staff."""

    def __init__(self, fifths: int) -> None:
        self.key_alters = key_signature_alters(fifths)
        self.current: Dict[Tuple[str, int], int] = {}

    def reset(self) -> None:
        self.current.clear()

    def apply(self, step: str, octave: int, alter: int, silent: bool = False) -> bool:
        """Record a spelling; return True when an accidental must be printed."""
        effective = self.current.get((step, octave), self.key_alters.get(step, 0))
        if effective == alter:
            return False
        self.current[(step, octave)] = alter
        return not silent


def compute_accidentals(
    measure_content: Dict[int, List[Fragment]],
    spelling: Dict[int, Tuple[str, int]],
    states: Dict[int, AccidentalState],
) -> None:
    """Decide, in time order across each staff, which notes print an accidental.

    Running the state machine in time order rather than voice order is what keeps
    a voice-2 note from being handed the accidental that a later voice-1 note
    already accounted for.
    """
    for staff, voices in STAFF_VOICES.items():
        state = states[staff]
        state.reset()
        events: List[Tuple[int, int, Fragment]] = []
        for voice in voices:
            for frag in measure_content.get(voice, []):
                if frag.kind == "note":
                    events.append((frag.on, voice, frag))
        events.sort(key=lambda item: (item[0], item[1]))
        for _tick, _voice, frag in events:
            frag.accidentals = {}
            for pitch in frag.pitches:
                step, alter, octave = spell_pitch(pitch, spelling)
                if state.apply(step, octave, alter, silent=frag.tie_in):
                    frag.accidentals[pitch] = alter


def emit_attributes(
    measure: ET.Element, fifths: int, mode: str, beats_per_bar: int
) -> None:
    """The one and only <attributes> block, in the order the DTD requires."""
    attributes = ET.SubElement(measure, "attributes")
    ET.SubElement(attributes, "divisions").text = str(DIVS)
    key = ET.SubElement(attributes, "key")
    ET.SubElement(key, "fifths").text = str(fifths)
    ET.SubElement(key, "mode").text = mode
    time = ET.SubElement(attributes, "time")
    ET.SubElement(time, "beats").text = str(beats_per_bar)
    ET.SubElement(time, "beat-type").text = "4"
    ET.SubElement(attributes, "staves").text = "2"
    for number, (sign, line) in ((1, ("G", 2)), (2, ("F", 4))):
        clef = ET.SubElement(attributes, "clef", {"number": str(number)})
        ET.SubElement(clef, "sign").text = sign
        ET.SubElement(clef, "line").text = str(line)


def emit_direction_metronome(measure: ET.Element, bpm: int) -> None:
    direction = ET.SubElement(measure, "direction", {"placement": "above"})
    dtype = ET.SubElement(direction, "direction-type")
    metronome = ET.SubElement(dtype, "metronome", {"parentheses": "no"})
    ET.SubElement(metronome, "beat-unit").text = "quarter"
    ET.SubElement(metronome, "per-minute").text = str(bpm)
    ET.SubElement(direction, "staff").text = "1"
    ET.SubElement(direction, "sound", {"tempo": str(bpm)})


def emit_direction_dynamics(measure: ET.Element, mark: str, staff: int) -> None:
    direction = ET.SubElement(measure, "direction", {"placement": "below"})
    dtype = ET.SubElement(direction, "direction-type")
    dynamics = ET.SubElement(dtype, "dynamics")
    ET.SubElement(dynamics, mark)
    ET.SubElement(direction, "staff").text = str(staff)
    ET.SubElement(direction, "sound", {"dynamics": str(DYNAMIC_SOUND.get(mark, 80))})


def emit_direction_pedal(measure: ET.Element, kind: str, staff: int) -> None:
    direction = ET.SubElement(measure, "direction", {"placement": "below"})
    dtype = ET.SubElement(direction, "direction-type")
    ET.SubElement(dtype, "pedal", {"type": kind, "line": "yes", "sign": "no"})
    ET.SubElement(direction, "staff").text = str(staff)


def emit_backup(measure: ET.Element, duration: int) -> None:
    backup = ET.SubElement(measure, "backup")
    ET.SubElement(backup, "duration").text = str(duration)


def emit_whole_measure_rest(measure: ET.Element, ctx: MeasureCtx, voice: int, staff: int) -> None:
    note = ET.SubElement(measure, "note")
    ET.SubElement(note, "rest", {"measure": "yes"})
    ET.SubElement(note, "duration").text = str(ctx.length)
    ET.SubElement(note, "voice").text = str(voice)
    ET.SubElement(note, "staff").text = str(staff)


def emit_note(
    measure: ET.Element,
    frag: Fragment,
    pitch: Optional[int],
    is_chord_member: bool,
    is_primary: bool,
    voice: int,
    staff: int,
    stem: Optional[str],
    spelling: Dict[int, Tuple[str, int]],
) -> None:
    """One <note> element, with children in the only order MusicXML permits."""
    note = ET.SubElement(measure, "note")
    if frag.invisible:
        note.set("print-object", "no")
    if is_chord_member:
        ET.SubElement(note, "chord")

    if pitch is None:
        rest = ET.SubElement(note, "rest")
        # A stem direction here means two voices share this staff, so both may be
        # resting at the same moment and a renderer has to place one rest above the
        # other.  Say which is which rather than leaving it to be inferred: left
        # unpinned, the two rests collide in the same space.
        if stem is not None:
            step, octave = TWO_VOICE_REST_POSITION[(staff, stem)]
            ET.SubElement(rest, "display-step").text = step
            ET.SubElement(rest, "display-octave").text = str(octave)
    else:
        step, alter, octave = spell_pitch(pitch, spelling)
        pitch_el = ET.SubElement(note, "pitch")
        ET.SubElement(pitch_el, "step").text = step
        if alter:
            ET.SubElement(pitch_el, "alter").text = str(alter)
        ET.SubElement(pitch_el, "octave").text = str(octave)

    ET.SubElement(note, "duration").text = str(frag.dur)

    tie_kinds: List[str] = []
    if pitch is not None:
        if frag.tie_in:
            tie_kinds.append("stop")
        if frag.tie_out:
            tie_kinds.append("start")
    for kind in tie_kinds:
        ET.SubElement(note, "tie", {"type": kind})

    ET.SubElement(note, "voice").text = str(voice)
    if frag.disp_type:
        ET.SubElement(note, "type").text = frag.disp_type
    for _ in range(frag.dots):
        ET.SubElement(note, "dot")

    if pitch is not None and pitch in frag.accidentals:
        ET.SubElement(note, "accidental").text = ACCIDENTAL_NAMES[frag.accidentals[pitch]]

    if frag.tmod is not None:
        actual, normal = frag.tmod
        tmod = ET.SubElement(note, "time-modification")
        ET.SubElement(tmod, "actual-notes").text = str(actual)
        ET.SubElement(tmod, "normal-notes").text = str(normal)

    if stem is not None and pitch is not None:
        ET.SubElement(note, "stem").text = stem

    ET.SubElement(note, "staff").text = str(staff)

    if is_primary and pitch is not None:
        for level in sorted(frag.beams):
            ET.SubElement(note, "beam", {"number": str(level)}).text = frag.beams[level]

    notations: List[ET.Element] = []
    tied_kinds = list(tie_kinds)
    tuplet_marks: List[str] = []
    if is_primary and frag.tuplet_mark:
        tuplet_marks = ["start", "stop"] if frag.tuplet_mark == "both" else [frag.tuplet_mark]
    if tied_kinds or tuplet_marks:
        notations_el = ET.SubElement(note, "notations")
        for kind in tied_kinds:
            ET.SubElement(notations_el, "tied", {"type": kind})
        for kind in tuplet_marks:
            ET.SubElement(notations_el, "tuplet", {"type": kind})
        notations.append(notations_el)


def emit_directions(
    measure: ET.Element,
    directions: Sequence[Tuple[int, str, str]],
    staff: int,
) -> None:
    """Write out directions in tick order."""
    for _tick, kind, payload in sorted(directions, key=lambda d: d[0]):
        if kind == "dynamics":
            emit_direction_dynamics(measure, payload, staff)
        elif kind == "pedal":
            emit_direction_pedal(measure, payload, staff)


def emit_voice(
    measure: ET.Element,
    frags: Sequence[Fragment],
    ctx: MeasureCtx,
    voice: int,
    staff: int,
    stem: Optional[str],
    spelling: Dict[int, Tuple[str, int]],
    directions: Sequence[Tuple[int, str, str]],
) -> None:
    """Emit one voice's notes for one measure, interleaving its directions."""
    pending = sorted(directions, key=lambda d: d[0])
    cursor = 0

    def flush(up_to: int) -> None:
        nonlocal cursor
        start = cursor
        while cursor < len(pending) and pending[cursor][0] <= up_to:
            cursor += 1
        emit_directions(measure, pending[start:cursor], staff)

    for frag in frags:
        flush(frag.on)
        if frag.kind == "rest":
            emit_note(measure, frag, None, False, True, voice, staff, stem, spelling)
            continue
        pitches = sorted(frag.pitches)
        for index, pitch in enumerate(pitches):
            emit_note(
                measure,
                frag,
                pitch,
                index > 0,
                index == 0,
                voice,
                staff,
                stem,
                spelling,
            )
    flush(ctx.start + ctx.length)


def build_score(
    measures: Sequence[MeasureCtx],
    content: Sequence[Dict[int, List[Fragment]]],
    spelling: Dict[int, Tuple[str, int]],
    fifths: int,
    is_major: bool,
    beats_per_bar: int,
    dynamics: Sequence[Tuple[int, str]],
    pedal_spans: Sequence[Tuple[int, int]],
    tempo_bpm: int,
    title: str,
) -> ET.Element:
    """Assemble the whole score-partwise document."""
    root = ET.Element("score-partwise", {"version": "3.1"})
    work = ET.SubElement(root, "work")
    ET.SubElement(work, "work-title").text = title
    identification = ET.SubElement(root, "identification")
    encoding = ET.SubElement(identification, "encoding")
    ET.SubElement(encoding, "encoding-date").text = _dt.date.today().isoformat()
    ET.SubElement(encoding, "software").text = "pianofi midiToXml"

    part_list = ET.SubElement(root, "part-list")
    score_part = ET.SubElement(part_list, "score-part", {"id": "P1"})
    ET.SubElement(score_part, "part-name", {"print-object": "no"}).text = "Piano"
    instrument = ET.SubElement(score_part, "score-instrument", {"id": "P1-I1"})
    ET.SubElement(instrument, "instrument-name").text = "Piano"
    midi = ET.SubElement(score_part, "midi-instrument", {"id": "P1-I1"})
    ET.SubElement(midi, "midi-channel").text = "1"
    ET.SubElement(midi, "midi-program").text = "1"

    part = ET.SubElement(root, "part", {"id": "P1"})
    states = {1: AccidentalState(fifths), 2: AccidentalState(fifths)}
    mode = "major" if is_major else "minor"

    dyn_by_measure: Dict[int, List[Tuple[int, str, str]]] = {}
    for tick, mark in dynamics:
        index = _measure_index(measures, tick)
        dyn_by_measure.setdefault(index, []).append((tick, "dynamics", mark))
    pedal_by_measure: Dict[int, List[Tuple[int, str, str]]] = {}
    for start, stop in pedal_spans:
        for tick, kind in ((start, "start"), (stop, "stop")):
            index = _measure_index(measures, tick)
            pedal_by_measure.setdefault(index, []).append((tick, "pedal", kind))

    for index, ctx in enumerate(measures):
        measure_content = content[index]
        compute_accidentals(measure_content, spelling, states)

        measure = ET.SubElement(part, "measure", {"number": str(ctx.number)})
        if ctx.implicit:
            measure.set("implicit", "yes")
        if index == 0:
            emit_attributes(measure, fifths, mode, beats_per_bar)
            emit_direction_metronome(measure, tempo_bpm)

        plan: List[Tuple[int, int]] = []
        for staff in (1, 2):
            primary, secondary = STAFF_VOICES[staff]
            plan.append((staff, primary))
            if measure_content.get(secondary):
                plan.append((staff, secondary))

        two_voice_staves = {
            staff for staff, voice in plan if voice == STAFF_VOICES[staff][1]
        }

        for position, (staff, voice) in enumerate(plan):
            if position > 0:
                emit_backup(measure, ctx.length)
            directions: List[Tuple[int, str, str]] = []
            if voice == STAFF_VOICES[1][0]:
                directions.extend(dyn_by_measure.get(index, []))
            if voice == STAFF_VOICES[2][0]:
                directions.extend(pedal_by_measure.get(index, []))
            frags = measure_content.get(voice) or []
            if not frags:
                # A bar this voice sits out still has to carry its directions:
                # dropping them would strand the other half of a pedal pair.
                emit_directions(measure, directions, staff)
                emit_whole_measure_rest(measure, ctx, voice, staff)
                continue
            stem: Optional[str] = None
            if staff in two_voice_staves:
                stem = "up" if voice == STAFF_VOICES[staff][0] else "down"
            emit_voice(
                measure, frags, ctx, voice, staff, stem, spelling, directions
            )

        if index == len(measures) - 1:
            barline = ET.SubElement(measure, "barline", {"location": "right"})
            ET.SubElement(barline, "bar-style").text = "light-heavy"

    return root


def serialize_score(root: ET.Element) -> str:
    """Pretty-print with the declaration and DOCTYPE both consumers expect."""
    _indent(root)
    body = ET.tostring(root, encoding="unicode")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" '
        '"http://www.musicxml.org/dtds/partwise.dtd">\n'
        + body
        + "\n"
    )


def _indent(element: ET.Element, level: int = 0) -> None:
    pad = "\n" + "  " * level
    if len(element):
        if not (element.text or "").strip():
            element.text = pad + "  "
        for child in element:
            _indent(child, level + 1)
        if not (element[-1].tail or "").strip():
            element[-1].tail = pad
    if level and not (element.tail or "").strip():
        element.tail = pad


# ---------------------------------------------------------------------------
# Stage 12 - self verification
# ---------------------------------------------------------------------------


class MusicXMLInvariantError(ValueError):
    """Raised when the emitted score violates a structural invariant."""


def _note_key(note: ET.Element) -> Optional[Tuple[str, int, int]]:
    pitch = note.find("pitch")
    if pitch is None:
        return None
    step = (pitch.findtext("step") or "").strip()
    octave = int(pitch.findtext("octave") or "0")
    alter = int(pitch.findtext("alter") or "0")
    return step, octave, alter


def _check_note_shape(note: ET.Element, number: str, problems: List[str]) -> None:
    tags = [child.tag for child in note]
    ranks = []
    for tag in tags:
        if tag not in NOTE_CHILD_ORDER:
            problems.append(f"measure {number}: <note> has unexpected child <{tag}>")
            return
        ranks.append(NOTE_CHILD_ORDER.index(tag))
    if any(b < a for a, b in zip(ranks, ranks[1:])):
        problems.append(f"measure {number}: <note> children out of order: {tags}")
    if "duration" not in tags:
        problems.append(f"measure {number}: <note> without <duration>")
    if "voice" not in tags:
        problems.append(f"measure {number}: <note> without <voice>")
    if "staff" not in tags:
        problems.append(f"measure {number}: <note> without <staff>")
    if ("pitch" in tags) == ("rest" in tags):
        problems.append(f"measure {number}: <note> must have exactly one of <pitch>/<rest>")

    note_type = note.findtext("type")
    duration = int(note.findtext("duration") or "0")
    dots = len(note.findall("dot"))
    tmod = note.find("time-modification")
    if tmod is not None:
        actual = int(tmod.findtext("actual-notes") or "0")
        normal = int(tmod.findtext("normal-notes") or "0")
        if actual <= 0 or normal <= 0:
            problems.append(f"measure {number}: bad <time-modification> {actual}/{normal}")
        elif (duration * actual) % normal != 0:
            problems.append(
                f"measure {number}: duration {duration} is not a {actual}:{normal} tuplet value"
            )
        else:
            equivalent = duration * actual // normal
            expected = DUPLE_DISPLAY.get(equivalent)
            if expected is None or expected != (note_type, dots):
                problems.append(
                    f"measure {number}: tuplet duration {duration} does not match "
                    f"type {note_type} with {dots} dot(s)"
                )
    elif note_type is not None:
        expected = DUPLE_DISPLAY.get(duration)
        if expected is None or expected != (note_type, dots):
            problems.append(
                f"measure {number}: duration {duration} does not match type "
                f"{note_type} with {dots} dot(s)"
            )


def check_invariants(root: ET.Element, cfg: Settings, repair: bool = True) -> List[str]:
    """Re-walk the finished document and prove it is engravable.

    This is the backstop for the whole module: it recomputes measure arithmetic
    from the DOM rather than trusting the code that produced it.  A duration
    *deficit* is padded with a rest and reported; overflow, ordering violations
    and dangling ties are fatal, because those are the errors that make a renderer
    silently drop or garble music.
    """
    problems: List[str] = []
    warnings: List[str] = []

    parts = root.findall("part")
    if len(parts) != 1:
        problems.append(f"expected exactly 1 part, found {len(parts)}")
    part = parts[0] if parts else ET.Element("part")

    measures = part.findall("measure")
    if not measures:
        problems.append("score has no measures")
    if len(measures) > cfg.max_measures:
        problems.append(f"score has {len(measures)} measures, over the cap")

    all_attributes = part.findall(".//attributes")
    if len(all_attributes) != 1:
        problems.append(f"expected exactly 1 <attributes>, found {len(all_attributes)}")
    elif measures and all_attributes[0] not in list(measures[0]):
        problems.append("<attributes> must appear in the first measure")
    divisions = part.findall(".//divisions")
    if len(divisions) != 1:
        problems.append(f"expected exactly 1 <divisions>, found {len(divisions)}")

    bar_length: Optional[int] = None
    time_el = part.find(".//attributes/time")
    if time_el is not None:
        beats = int(time_el.findtext("beats") or "4")
        beat_type = int(time_el.findtext("beat-type") or "4")
        bar_length = beats * (DIVS * 4 // beat_type)

    open_ties: Dict[Tuple[int, str, int, int], int] = {}

    for measure in measures:
        number = measure.get("number", "?")
        implicit = measure.get("implicit") == "yes"
        cursor = 0
        max_cursor = 0
        voice_sums: Dict[int, int] = {}
        voice_last_index: Dict[int, int] = {}
        voice_staff: Dict[int, int] = {}
        tuplet_depth: Dict[int, int] = {}
        previous: Optional[Tuple[int, int, int]] = None

        for position, child in enumerate(list(measure)):
            if child.tag == "forward":
                problems.append(
                    f"measure {number}: <forward> is never emitted (padding rests are used instead)"
                )
                continue
            if child.tag == "backup":
                cursor -= int(child.findtext("duration") or "0")
                if cursor < 0:
                    problems.append(f"measure {number}: <backup> moves the cursor before bar start")
                continue
            if child.tag != "note":
                continue

            _check_note_shape(child, number, problems)
            duration = int(child.findtext("duration") or "0")
            voice = int(child.findtext("voice") or "0")
            staff = int(child.findtext("staff") or "0")
            is_chord = child.find("chord") is not None

            if is_chord:
                if previous is None or (duration, voice, staff) != previous:
                    problems.append(
                        f"measure {number}: chord member disagrees with its primary note "
                        f"(duration/voice/staff {duration}/{voice}/{staff} vs {previous})"
                    )
            else:
                cursor += duration
                max_cursor = max(max_cursor, cursor)
                voice_sums[voice] = voice_sums.get(voice, 0) + duration
                voice_last_index[voice] = position
                voice_staff[voice] = staff
                previous = (duration, voice, staff)

            for tie in child.findall("tie"):
                key = _note_key(child)
                if key is None:
                    problems.append(f"measure {number}: <tie> on a rest")
                    continue
                tie_key = (voice, key[0], key[1], key[2])
                if tie.get("type") == "start":
                    open_ties[tie_key] = open_ties.get(tie_key, 0) + 1
                else:
                    if open_ties.get(tie_key, 0) <= 0:
                        problems.append(
                            f"measure {number}: tie stop with no matching start on "
                            f"{key[0]}{key[2]:+d}/{key[1]} voice {voice}"
                        )
                    else:
                        open_ties[tie_key] -= 1

            notations = child.find("notations")
            if notations is not None:
                for tuplet in notations.findall("tuplet"):
                    if tuplet.get("type") == "start":
                        tuplet_depth[voice] = tuplet_depth.get(voice, 0) + 1
                    else:
                        tuplet_depth[voice] = tuplet_depth.get(voice, 0) - 1
                        if tuplet_depth[voice] < 0:
                            problems.append(
                                f"measure {number}: tuplet stop with no matching start"
                            )

        for voice, depth in tuplet_depth.items():
            if depth != 0:
                problems.append(f"measure {number}: unbalanced tuplet bracket in voice {voice}")

        expected = max_cursor
        if bar_length is not None and not implicit:
            expected = bar_length
        if bar_length is not None and implicit and max_cursor > bar_length:
            problems.append(
                f"measure {number}: pickup of {max_cursor} exceeds the bar length {bar_length}"
            )

        for voice in sorted(voice_sums):
            total = voice_sums[voice]
            if total > expected:
                problems.append(
                    f"measure {number}: voice {voice} sums to {total}, over the "
                    f"measure length {expected}"
                )
            elif total < expected:
                deficit = expected - total
                warnings.append(
                    f"measure {number}: padded voice {voice} with {deficit} tick(s) of rest"
                )
                if repair:
                    _insert_pad_rest(
                        measure,
                        voice_last_index[voice] + 1,
                        deficit,
                        voice,
                        voice_staff.get(voice, 1),
                    )
        if cursor != expected:
            problems.append(
                f"measure {number}: cursor ends at {cursor}, expected {expected}"
            )

    for key, depth in open_ties.items():
        if depth != 0:
            problems.append(
                f"unterminated tie on {key[1]}{key[3]:+d}/{key[2]} voice {key[0]}"
            )

    for message in warnings:
        logging.warning("MusicXML repair: %s", message)
    if problems:
        summary = "; ".join(problems[:12])
        if len(problems) > 12:
            summary += f"; ... and {len(problems) - 12} more"
        raise MusicXMLInvariantError(f"MusicXML invariant check failed: {summary}")
    return warnings


def _insert_pad_rest(
    measure: ET.Element, index: int, duration: int, voice: int, staff: int
) -> None:
    note = ET.Element("note")
    ET.SubElement(note, "rest")
    ET.SubElement(note, "duration").text = str(duration)
    ET.SubElement(note, "voice").text = str(voice)
    ET.SubElement(note, "staff").text = str(staff)
    measure.insert(index, note)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def convert_midi_to_xml(
    midi_file_path,
    output_path,
    job_id=None,
    sheet_music_title=None,
    cfg: Optional[Settings] = None,
) -> str:
    """Convert a MIDI file to MusicXML.

    Args:
        midi_file_path: Path to the input MIDI file.
        output_path: Path the MusicXML file is written to.
        job_id: Optional identifier, logged so a run can be traced.
        sheet_music_title: Optional title; defaults to "Piano Transcription".
        cfg: Optional Settings override.

    Returns:
        str: ``output_path``, for the caller to hand on.

    Raises:
        ValueError: The MIDI contains no usable notes, or the emitted score
            failed its own invariant check.
    """
    cfg = cfg or Settings()
    midi_file_path = Path(midi_file_path)
    output_path = Path(output_path)
    logging.info("Converting MIDI to MusicXML for job %s", job_id)

    if not midi_file_path.exists():
        raise FileNotFoundError(f"Input MIDI file not found: {midi_file_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    parsed = parse_midi(str(midi_file_path), cfg)
    grid = choose_grid(parsed, cfg)
    beats_per_bar, downbeat_beat, _meter_source = detect_meter(parsed, grid, cfg)
    subdiv = choose_subdivisions(parsed, grid, cfg)
    qnotes = clean_quantized(quantize(parsed, grid, subdiv, cfg), cfg)

    assign_hands(qnotes, cfg)
    legato_fill(qnotes, cfg)
    tonic, is_major, fifths = detect_key(qnotes)
    spelling = build_spelling(tonic, is_major, fifths)

    voice_streams: Dict[int, List[VoiceEvent]] = {}
    for staff in (1, 2):
        primary, secondary = STAFF_VOICES[staff]
        upper, lower = separate_voices([q for q in qnotes if q.staff == staff], cfg)
        voice_streams[primary] = upper
        voice_streams[secondary] = lower
    n_second = sum(1 for v in (2, 6) if voice_streams.get(v))
    logging.info("Voices: %d staff(s) need a second voice", n_second)

    first_tick = min(q.on for q in qnotes)
    last_tick = max(q.off for q in qnotes)
    measures = plan_measures(
        first_tick, last_tick, beats_per_bar, downbeat_beat * DIVS, cfg
    )
    content = assemble_measures(voice_streams, measures, subdiv)

    dynamics = compute_dynamics(qnotes, cfg)
    score_start = measures[0].start
    score_end = measures[-1].start + measures[-1].length
    # The pedal line rides the lower staff's primary voice, so those are the
    # positions a pedal mark can be attached to.  Bars where that voice rests
    # wholesale contribute their barline, which is where the rest sits.
    # The final barline joins them, so a pedal held to the end can be released there.
    pedal_voice = STAFF_VOICES[2][0]
    pedal_anchors = {ctx.start for ctx in measures} | {score_end}
    for measure_content in content:
        for frag in measure_content.get(pedal_voice) or ():
            pedal_anchors.add(frag.on)
    pedal_spans = quantize_pedal(
        parsed, grid, sorted(pedal_anchors), score_start, score_end, cfg
    )
    tempo_bpm = pick_tempo_bpm(grid)

    root = build_score(
        measures=measures,
        content=content,
        spelling=spelling,
        fifths=fifths,
        is_major=is_major,
        beats_per_bar=beats_per_bar,
        dynamics=dynamics,
        pedal_spans=pedal_spans,
        tempo_bpm=tempo_bpm,
        title=sheet_music_title or "Piano Transcription",
    )
    check_invariants(root, cfg, repair=True)

    output_path.write_text(serialize_score(root), encoding="utf-8")
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise IOError(f"Failed to write MusicXML file at {output_path}")
    logging.info(
        "Wrote MusicXML for job %s: %s (%d measure(s), %d byte(s))",
        job_id,
        output_path,
        len(measures),
        output_path.stat().st_size,
    )
    return str(output_path)


def check_musicxml_file(path, cfg: Optional[Settings] = None) -> List[str]:
    """Re-run the invariant check against an existing MusicXML file."""
    cfg = cfg or Settings()
    tree = ET.parse(str(path))
    warnings = check_invariants(tree.getroot(), cfg, repair=False)
    root = tree.getroot()
    measures = root.findall("./part/measure")
    notes = root.findall(".//note")
    logging.info(
        "%s: %d measure(s), %d note element(s), invariants OK%s",
        path,
        len(measures),
        len(notes),
        f" ({len(warnings)} warning(s))" if warnings else "",
    )
    return warnings


# ---------------------------------------------------------------------------
# Self test
# ---------------------------------------------------------------------------
#
# Ten fixtures, each built with mido so the exact tick layout is known, then
# converted and asserted on.  They cover the cases that broke the previous
# converter: notes that outlive the next onset, notes that cross barlines,
# triplets, pickup bars, two voices on one staff, and same-pitch overlaps.


def _jitter_sequence(count: int, amplitude: float, seed: int = 12345) -> List[float]:
    """Deterministic pseudo-random jitter, so the selftest never flakes."""
    values: List[float] = []
    state = seed
    for _ in range(count):
        state = (1103515245 * state + 12345) % (2 ** 31)
        values.append(((state / (2 ** 31)) * 2.0 - 1.0) * amplitude)
    return values


def _build_midi(
    path,
    notes: Sequence[Tuple[int, int, int, int]],
    bpm: float = 120.0,
    ppq: int = 480,
    numerator: int = 4,
    denominator: int = 4,
    cc64: Sequence[Tuple[int, int]] = (),
    tempo_map: Optional[Sequence[Tuple[int, float]]] = None,
) -> None:
    """Write a MIDI file from absolute-tick ``(on, off, pitch, velocity)`` notes."""
    import mido

    mid = mido.MidiFile(type=1, ticks_per_beat=ppq)
    meta_track = mido.MidiTrack()
    mid.tracks.append(meta_track)

    meta_events: List[Tuple[int, int, "mido.Message"]] = []
    if tempo_map:
        for tick, value in tempo_map:
            meta_events.append(
                (tick, 0, mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(value)))
            )
    else:
        meta_events.append(
            (0, 0, mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm)))
        )
    meta_events.append(
        (
            0,
            1,
            mido.MetaMessage(
                "time_signature", numerator=numerator, denominator=denominator
            ),
        )
    )
    _append_sorted(meta_track, meta_events)

    note_events: List[Tuple[int, int, "mido.Message"]] = []
    for on, off, pitch, velocity in notes:
        note_events.append(
            (on, 1, mido.Message("note_on", note=pitch, velocity=velocity, channel=0))
        )
        note_events.append(
            (off, 0, mido.Message("note_off", note=pitch, velocity=0, channel=0))
        )
    for tick, value in cc64:
        note_events.append(
            (tick, 2, mido.Message("control_change", control=64, value=value, channel=0))
        )
    note_track = mido.MidiTrack()
    mid.tracks.append(note_track)
    _append_sorted(note_track, note_events)

    mid.save(str(path))


def _append_sorted(track, events) -> None:
    events.sort(key=lambda item: (item[0], item[1]))
    previous = 0
    for tick, _order, message in events:
        message.time = max(tick - previous, 0)
        track.append(message)
        previous = tick


_SCALE_PITCHES = (
    60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79, 81, 83, 84,
    83, 81, 79, 77, 76, 74, 72, 71, 69, 67, 65, 64, 62,
)


def _fx_scale(path) -> None:
    """A scale played at 92 BPM inside a file that claims a flat 120 BPM.

    This is the wall-clock producer archetype: the tempo map is an unset default,
    so the grid has to be recovered from the onsets themselves.
    """
    seconds_per_beat = 60.0 / 92.0
    ticks_per_second = 480 * 2  # a flat 120 BPM map at PPQ 480
    jitter = _jitter_sequence(len(_SCALE_PITCHES), 0.020)
    notes = []
    for i, pitch in enumerate(_SCALE_PITCHES):
        onset = i * seconds_per_beat + jitter[i]
        on = max(int(round(onset * ticks_per_second)), 0)
        off = on + int(round(0.9 * seconds_per_beat * ticks_per_second))
        notes.append((on, off, pitch, 70 + (i % 5) * 3))
    _build_midi(path, notes, bpm=120.0)


def _fx_chords_dotted(path) -> None:
    """Block chords in a dotted-quarter / eighth rhythm, on an exact tick grid."""
    notes = []
    chords = ((60, 64, 67), (59, 62, 67), (57, 60, 65), (55, 59, 62))
    tick = 0
    for _bar in range(4):
        for index, chord in enumerate(chords):
            dur = 720 if index % 2 == 0 else 240
            for pitch in chord:
                notes.append((tick, tick + dur, pitch, 78))
            tick += dur
    _build_midi(path, notes, bpm=100.0)


def _fx_triplets(path) -> None:
    """Straight eighths on beats 1 and 3, eighth triplets on beats 2 and 4."""
    notes = []
    for bar in range(4):
        base = bar * 1920
        for beat in range(4):
            start = base + beat * 480
            if beat % 2 == 0:
                for k in range(2):
                    notes.append((start + k * 240, start + k * 240 + 240, 60 + 2 * k, 80))
            else:
                for k in range(3):
                    notes.append((start + k * 160, start + k * 160 + 160, 64 + 2 * k, 80))
    _build_midi(path, notes, bpm=100.0)


def _fx_cross_barline(path) -> None:
    """A chord struck on the last beat of each bar and held into the next.

    The previous converter clipped exactly this case; here it has to come out as
    a tie.
    """
    notes = []
    for bar in range(5):
        base = bar * 1920
        notes.append((base, base + 480, 36, 84))          # bass marks the downbeat
        notes.append((base + 480, base + 960, 74, 76))
        notes.append((base + 960, base + 1440, 76, 76))
        # Struck on beat 4 and held two beats, so it lands on the next downbeat.
        notes.append((base + 1440, base + 2400, 79, 76))
    _build_midi(path, notes, bpm=100.0)


def _fx_velocity_ramp(path) -> None:
    """Sixty-four quarter notes ramping from very soft to very loud."""
    notes = []
    count = 64
    for i in range(count):
        on = i * 480
        velocity = int(round(20 + (110 - 20) * i / (count - 1)))
        notes.append((on, on + 460, 60 + (i % 7), max(1, min(velocity, 127))))
    _build_midi(path, notes, bpm=100.0)


def _fx_pedal(path) -> None:
    """Chords with chattering CC64: two real presses plus noise to debounce away."""
    notes = []
    for bar in range(4):
        base = bar * 1920
        for beat in range(4):
            start = base + beat * 480
            for pitch in (48, 55, 64):
                notes.append((start, start + 470, pitch, 76))
    # One press over bars 1-2 and another over bars 3-4, each surrounded by
    # chatter.  The lift between them is half a second, well clear of the 100 ms
    # merge window, so it has to survive as a real re-pedal.
    cc = [
        (0, 100), (10, 0), (12, 110),   # bounce on the way down
        (3800, 0),
        (4200, 96), (4210, 20), (4220, 100),
        (7600, 0),
    ]
    _build_midi(path, notes, bpm=100.0, cc64=cc)


def _fx_waltz_pickup(path) -> None:
    """A 3/4 waltz that starts on beat 3 of an implied bar, so measure 0 is a pickup."""
    notes = [(960, 1440, 67, 70)]  # single pickup quarter
    for bar in range(4):
        base = 1440 + bar * 1440
        notes.append((base, base + 460, 48, 82))
        for beat in (1, 2):
            start = base + beat * 480
            for pitch in (60, 64):
                notes.append((start, start + 440, pitch, 66))
    _build_midi(path, notes, bpm=96.0, numerator=3, denominator=4)


def _fx_two_voice(path) -> None:
    """A sustained inner line under moving eighths, both inside one hand's span."""
    notes = []
    for half in range(8):
        base = half * 960
        notes.append((base, base + 960, 76, 80))
        for k, pitch in enumerate((71, 72, 74, 75)):
            on = base + k * 240
            notes.append((on, on + 240, pitch, 72))
    _build_midi(path, notes, bpm=100.0)


def _fx_single_note(path) -> None:
    """One whole note: the degenerate input that used to divide by zero."""
    _build_midi(path, [(0, 1920, 60, 72)], bpm=100.0)


def _fx_same_pitch_overlap(path) -> None:
    """A repeated pitch re-struck before its predecessor released."""
    notes = []
    for bar in range(4):
        base = bar * 1920
        notes.append((base, base + 960, 60, 80))
        notes.append((base + 480, base + 1440, 60, 84))
        notes.append((base + 960, base + 1920, 67, 74))
    _build_midi(path, notes, bpm=100.0)


# --- assertions -------------------------------------------------------------


def _tags(root: ET.Element, tag: str) -> List[ET.Element]:
    return list(root.iter(tag))


def _dynamic_marks(root: ET.Element) -> List[str]:
    marks: List[str] = []
    for dynamics in root.iter("dynamics"):
        for child in dynamics:
            marks.append(child.tag)
    return marks


def _pedal_types(root: ET.Element) -> List[str]:
    return [p.get("type", "") for p in root.iter("pedal")]


def _note_types(root: ET.Element) -> List[Tuple[str, int]]:
    out: List[Tuple[str, int]] = []
    for note in root.iter("note"):
        type_el = note.find("type")
        if type_el is not None and type_el.text:
            out.append((type_el.text, len(note.findall("dot"))))
    return out


def _check_scale(root: ET.Element) -> None:
    fifths = root.find(".//key/fifths")
    mode = root.find(".//key/mode")
    assert fifths is not None and fifths.text == "0", f"expected C major, got fifths={fifths}"
    assert mode is not None and mode.text == "major", "expected major mode"
    per_minute = root.find(".//metronome/per-minute")
    assert per_minute is not None, "no metronome emitted"
    bpm = int(per_minute.text or "0")
    assert 86 <= bpm <= 98, f"expected the real ~92 BPM to be recovered, got {bpm}"


def _check_chords_dotted(root: ET.Element) -> None:
    types = _note_types(root)
    assert any(t == "quarter" and dots == 1 for t, dots in types), "no dotted quarters"
    assert len(_tags(root, "chord")) >= 8, "chords were flattened"


def _check_triplets(root: ET.Element) -> None:
    ratios = [
        (
            (tm.findtext("actual-notes") or ""),
            (tm.findtext("normal-notes") or ""),
        )
        for tm in root.iter("time-modification")
    ]
    assert ("3", "2") in ratios, f"no 3:2 time-modification, saw {set(ratios)}"
    marks = [t.get("type") for t in root.iter("tuplet")]
    assert marks.count("start") == marks.count("stop"), f"unbalanced tuplets: {marks}"
    assert marks.count("start") >= 4, "expected a tuplet bracket per triplet beat"


def _check_cross_barline(root: ET.Element) -> None:
    types = [t.get("type") for t in root.iter("tie")]
    starts, stops = types.count("start"), types.count("stop")
    assert starts == stops, f"unbalanced ties: {starts} start / {stops} stop"
    assert starts >= 4, f"sustains were clipped at barlines instead of tied ({starts})"
    tied = [t.get("type") for t in root.iter("tied")]
    assert tied.count("start") == starts and tied.count("stop") == stops, "notation/tie mismatch"


def _check_velocity_ramp(root: ET.Element) -> None:
    marks = _dynamic_marks(root)
    assert len(marks) >= 3, f"velocity ramp produced too few dynamics: {marks}"
    loudness = [DYNAMIC_SOUND[m] for m in marks]
    assert loudness == sorted(loudness), f"dynamics are not ordered: {marks}"
    assert loudness[-1] > loudness[0], "ramp did not get louder"


def _check_pedal(root: ET.Element) -> None:
    types = _pedal_types(root)
    assert types.count("start") == types.count("stop"), f"unbalanced pedal: {types}"
    assert types.count("start") >= 2, f"pedal presses were lost: {types}"
    assert types.count("start") <= 4, f"pedal chatter was not debounced: {types}"


def _check_waltz_pickup(root: ET.Element) -> None:
    beats = root.find(".//time/beats")
    assert beats is not None and beats.text == "3", f"expected 3/4, got {beats}"
    first = root.find(".//part/measure")
    assert first is not None
    assert first.get("number") == "0", f"pickup not numbered 0: {first.get('number')}"
    assert first.get("implicit") == "yes", "pickup measure not marked implicit"


def _check_two_voice(root: ET.Element) -> None:
    voices = {v.text for v in root.iter("voice")}
    assert "2" in voices, f"second voice missing, saw {sorted(voices)}"
    stems = {s.text for s in root.iter("stem")}
    assert {"up", "down"} <= stems, f"expected opposed stems, saw {stems}"


def _check_single_note(root: ET.Element) -> None:
    measures = _tags(root, "measure")
    assert len(measures) >= 1, "no measures emitted"


def _check_same_pitch_overlap(root: ET.Element) -> None:
    assert len(_tags(root, "note")) >= 4, "notes were dropped"


_Builder = Callable[[Path], None]
_Checker = Callable[[ET.Element], None]

_FIXTURES: Tuple[Tuple[str, _Builder, _Checker], ...] = (
    ("scale_fake_tempo", _fx_scale, _check_scale),
    ("chords_dotted", _fx_chords_dotted, _check_chords_dotted),
    ("triplets", _fx_triplets, _check_triplets),
    ("cross_barline", _fx_cross_barline, _check_cross_barline),
    ("velocity_ramp", _fx_velocity_ramp, _check_velocity_ramp),
    ("pedal_chatter", _fx_pedal, _check_pedal),
    ("waltz_pickup", _fx_waltz_pickup, _check_waltz_pickup),
    ("two_voice", _fx_two_voice, _check_two_voice),
    ("single_note", _fx_single_note, _check_single_note),
    ("same_pitch_overlap", _fx_same_pitch_overlap, _check_same_pitch_overlap),
)


def _check_universal(root: ET.Element) -> None:
    """Assertions that must hold for every fixture."""
    parts = _tags(root, "part")
    assert len(parts) == 1, f"expected one piano part, got {len(parts)}"
    staves = root.find(".//attributes/staves")
    assert staves is not None and staves.text == "2", "grand staff missing"
    assert not _tags(root, "forward"), "<forward> is not safe for musicxml2ly"
    assert _tags(root, "measure"), "no measures"
    title = root.find("./work/work-title")
    assert title is not None and title.text, "OSMD needs a work-title"


def _selftest() -> int:
    """Build, convert and verify every fixture.  Returns a process exit code."""
    import tempfile

    try:
        import mido  # noqa: F401
    except ImportError:
        print("selftest requires mido (pip install mido==1.3.3)")
        return 2

    results: List[Tuple[str, bool, str]] = []
    with tempfile.TemporaryDirectory(prefix="midixml-selftest-") as tmp:
        root_dir = Path(tmp)
        for name, builder, checker in _FIXTURES:
            midi_path = root_dir / f"{name}.mid"
            xml_path = root_dir / f"{name}.musicxml"
            try:
                builder(midi_path)
                convert_midi_to_xml(
                    midi_path,
                    xml_path,
                    job_id=f"selftest-{name}",
                    sheet_music_title=name.replace("_", " ").title(),
                )
                tree = ET.parse(xml_path)
                root = tree.getroot()
                check_invariants(root, Settings(), repair=False)
                _check_universal(root)
                checker(root)
            except Exception as exc:  # noqa: BLE001 - the point is to report anything
                results.append((name, False, f"{type(exc).__name__}: {exc}"))
            else:
                measures = len(list(root.iter("measure")))
                notes = len(list(root.iter("note")))
                results.append((name, True, f"{measures} measures, {notes} notes"))

    width = max(len(name) for name, _ok, _detail in results)
    print("")
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {detail}")
    failed = [name for name, ok, _detail in results if not ok]
    print("")
    print(f"{len(results) - len(failed)}/{len(results)} fixtures passed")
    return 1 if failed else 0


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

_USAGE = """\
usage:
  python midiToXml.py <input.mid> <output.musicxml> [title]
  python midiToXml.py --selftest
  python midiToXml.py --check <file.musicxml> [more.musicxml ...]
"""


def main(argv: Optional[Sequence[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(_USAGE, end="")
        return 1

    if args[0] == "--selftest":
        return _selftest()

    if args[0] == "--check":
        targets = args[1:]
        if not targets:
            print(_USAGE, end="")
            return 1
        failed = False
        for target in targets:
            try:
                warnings = check_musicxml_file(target)
            except (MusicXMLInvariantError, ET.ParseError, OSError) as exc:
                logging.error("%s: %s", target, exc)
                failed = True
            else:
                status = f"{len(warnings)} warning(s)" if warnings else "clean"
                print(f"OK   {target}  ({status})")
        return 1 if failed else 0

    if len(args) < 2:
        print(_USAGE, end="")
        return 1

    title = args[2] if len(args) >= 3 else None
    try:
        result = convert_midi_to_xml(args[0], args[1], sheet_music_title=title)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        logging.error("Conversion failed: %s", exc)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
