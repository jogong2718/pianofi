import os
import subprocess
import logging
from pathlib import Path
import sys

from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH

def run_basicpitch(audio_file, output_file):
    """
    Process audio file with BasicPitch and generate MIDI file
    
    Args:
        audio_file (str): Path to the input audio file
        output_file (str): Path to output MIDI file (e.g., "/tmp/job123.midi")
        
    Returns:
        Path: Path to the generated MIDI file
    """
    logging.info(f"Running BasicPitch on {audio_file}, output to {output_file}")
    audio_file = Path(audio_file)
    output_file = Path(output_file)
    output_dir = output_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)


    original_dir = os.getcwd()
    logging.info(f"Original working directory: {original_dir}")
    
    try:
        # Run BasicPitch inference
        _, midi_data, _ = predict(str(audio_file))

        # Save MIDI data to output file
        with open(output_file, "wb") as f:
            f.write(midi_data)
        
        logging.info(f"BasicPitch output saved to {output_file}")
        
        # Move/rename to the desired output file path
        if output_file.exists():
            logging.info(f"Generated MIDI file at {output_file}")
            return output_file
        else:
            raise FileNotFoundError(f"BasicPitch did not generate MIDI file at {output_file}")
        
    except subprocess.CalledProcessError as e:
        logging.error(f"BasicPitch failed: {e.stderr}")
        raise Exception(f"BasicPitch processing failed: {e}")
    except Exception as e:
        logging.error(f"Error running BasicPitch: {e}")
        raise
    finally:
        os.chdir(original_dir)
        logging.info(f"Restored working directory to: {os.getcwd()}")