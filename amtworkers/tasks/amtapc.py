import os
import subprocess
import logging
from pathlib import Path
import sys

def run_amtapc(audio_file, output_file, style="level3"):
    """
    Process audio file with AMT-APC and generate MIDI file
    
    Args:
        audio_file (str): Path to the input audio file
        output_file (str): Path to output MIDI file (e.g., "/tmp/job123.midi")
        style (str): Piano cover style (level1, level2, level3)
        
    Returns:
        Path: Path to the generated MIDI file
    """
    logging.info(f"Running AMT-APC on {audio_file} with style {style}")
    audio_file = Path(audio_file)
    output_file = Path(output_file)
    output_dir = output_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure we're in the correct directory for the AMT-APC script
    amt_apc_dir = Path("/app/amt-apc")
    model_file = amt_apc_dir / "models" / "params" / "apc.pth"

    if not amt_apc_dir.exists():
        raise FileNotFoundError(f"AMT-APC directory {amt_apc_dir} does not exist")
    
    if not model_file.exists():
        raise FileNotFoundError(f"Model file {model_file} does not exist. Please ensure it is downloaded.")
    
    logging.info(f"Using model file: {model_file}")


    original_dir = os.getcwd()
    logging.info(f"Original working directory: {original_dir}")
    
    try:
        # Run AMT-APC inference
        os.chdir(amt_apc_dir)
        logging.info(f"Current working directory: {os.getcwd()}")

        style_level = f"level{style}"

        # Command to run AMT-APC inference
        cmd = [
            sys.executable,
            "infer",  # No .py extension
            str(audio_file),
            "--style", style_level,
            "--output", str(output_file),
            "--path_model", str(model_file)  # Add explicit model path
        ]

        logging.info(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logging.info(f"AMT-APC output: {result.stdout}")
        
        # Move/rename to the desired output file path
        if output_file.exists():
            logging.info(f"Generated MIDI file at {output_file}")
            return output_file
        else:
            raise FileNotFoundError(f"AMT-APC did not generate MIDI file at {output_file}")
        
    except subprocess.CalledProcessError as e:
        logging.error(f"AMT-APC failed: {e.stderr}")
        raise Exception(f"AMT-APC processing failed: {e}")
    except Exception as e:
        logging.error(f"Error running AMT-APC: {e}")
        raise
    finally:
        os.chdir(original_dir)
        logging.info(f"Restored working directory to: {os.getcwd()}")