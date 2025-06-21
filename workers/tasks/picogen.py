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
    output_dir = output_dir # output directory

    tokenizer = picogen2.Tokenizer()
    model = picogen2.PiCoGenDecoder.from_pretrained(device="cpu")

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

    (Path(output_dir.name) / "piano.txt").write_text("\n".join(map(str, out_events)))
    tokenizer.events_to_midi(out_events).dump(Path(output_dir.name) / "piano.mid")

    return Path(output_dir.name) / "piano.mid"