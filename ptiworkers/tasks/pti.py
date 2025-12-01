import os
import logging
from pathlib import Path

import librosa
import pretty_midi
from piano_transcription_inference import PianoTranscription, sample_rate

def run_pti(audio_file, output_file):
    """
    Process audio file with piano_transcription_inference and generate MIDI file
    
    Args:
        audio_file (str): Path to the input audio file
        output_file (str): Path to output MIDI file (e.g., "/tmp/job123.midi")
    Returns:
        Path: Path to the generated MIDI file
    """
    logging.info(f"Running piano_transcription_inference on {audio_file}, output to {output_file}")
    audio_file = Path(audio_file)
    output_file = Path(output_file)
    output_dir = output_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Load audio with librosa at the required sample rate
        audio, _ = librosa.load(str(audio_file), sr=sample_rate, mono=True)
        
        # Create transcriptor with CPU
        transcriptor = PianoTranscription(device='cpu', checkpoint_path=None)
        
        # Transcribe and write out to MIDI file
        transcriptor.transcribe(audio, str(output_file))
        
        logging.info(f"Transcription output saved to {output_file}")
        
        # Load the MIDI file to set instrument to Acoustic Grand Piano
        midi_data = pretty_midi.PrettyMIDI(str(output_file))
        for instrument in midi_data.instruments:
            logging.info(f"Original instrument: program={instrument.program}, is_drum={instrument.is_drum}, name='{instrument.name}'")
            instrument.program = 0  # Acoustic Grand Piano
            instrument.is_drum = False
            instrument.name = "Acoustic Grand Piano"
            logging.info(f"Changed to: program={instrument.program}, name='{instrument.name}'")
        
        # Save the modified MIDI file
        midi_data.write(str(output_file))
        
        if output_file.exists():
            logging.info(f"Generated MIDI file at {output_file}")
            return output_file
        else:
            raise FileNotFoundError(f"piano_transcription_inference did not generate MIDI file at {output_file}")
        
    except Exception as e:
        logging.error(f"Error running piano_transcription_inference: {e}")
        raise