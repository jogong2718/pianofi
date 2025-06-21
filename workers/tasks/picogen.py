import os
import sys
from pathlib import Path
import subprocess
import logging
from collections import Counter
import tempfile

from mirtoolkit import beat_this, sheetsage
import picogen2

def run_picogen(audio_file, output_dir):
    audio_file = audio_file # input file
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    tokenizer = picogen2.Tokenizer()
    model = picogen2.PiCoGenDecoder.from_pretrained(device="cuda")

    beats, downbeats = beat_this.detect(audio_file)
    beat_information = {"beats": beats.tolist(), "downbeats": downbeats.tolist()}

    # extract feature
    sheetsage_output = sheetsage.infer(audio_path=audio_file, beat_information=beat_information)

    # generate piano cover
    out_events = picogen2.decode(
        model=model,
        tokenizer=tokenizer,
        beat_information=beat_information,
        melody_last_embs=sheetsage_output["melody_last_hidden_state"],
        harmony_last_embs=sheetsage_output["harmony_last_hidden_state"],
    )

    (output_path / "piano.txt").write_text("\n".join(map(str, out_events)))
    
    midi_file_path = output_path / "piano.mid"
    tokenizer.events_to_midi(out_events).dump(midi_file_path)

    return midi_file_path