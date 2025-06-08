import os
import sys
import torch as th
import torchaudio as ta
from pathlib import Path
import subprocess
import logging

from demucs.apply import apply_model, BagOfModels
from demucs.audio import AudioFile, convert_audio, save_audio
from demucs.htdemucs import HTDemucs
from demucs.pretrained import get_model

def load_track(track_path, audio_channels=2, samplerate=44100):
    """
    Load audio track using multiple backends for reliability
    Based on the Demucs load_track function
    """
    errors = {}
    wav = None
    track = Path(track_path)

    # Try AudioFile (FFmpeg) first - most reliable
    try:
        wav = AudioFile(track).read(
            streams=0,
            samplerate=samplerate,
            channels=audio_channels
        )
        logging.info(f"✅ Loaded {track} using FFmpeg")
    except FileNotFoundError:
        errors['ffmpeg'] = 'FFmpeg is not installed.'
    except subprocess.CalledProcessError:
        errors['ffmpeg'] = 'FFmpeg could not read the file.'

    # Fallback to torchaudio if FFmpeg fails
    if wav is None:
        try:
            wav, sr = ta.load(str(track))
            wav = convert_audio(wav, sr, samplerate, audio_channels)
            logging.info(f"✅ Loaded {track} using torchaudio")
        except RuntimeError as err:
            errors['torchaudio'] = str(err)

    # If both methods fail, raise an error
    if wav is None:
        error_msg = f"Could not load file {track}. Maybe it is not a supported file format?"
        for backend, error in errors.items():
            error_msg += f"\nWhen trying to load using {backend}, got the following error: {error}"
        raise Exception(error_msg)
    
    return wav

def separate_stems(input_file: str, output_dir: str, model_name: str = "htdemucs") -> dict:
    """
    High-quality audio stem separation using Demucs
    
    Args:
        input_file: Path to input audio file
        output_dir: Directory to save separated stems
        model_name: Demucs model to use (htdemucs, htdemucs_ft, mdx_extra, etc.)
    
    Returns:
        Dictionary mapping stem names to file paths
    """
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Check if input file exists
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file {input_file} does not exist")
    
    logging.info(f"🎵 Starting stem separation for: {input_file}")
    logging.info(f"📁 Output directory: {output_dir}")
    logging.info(f"🤖 Using model: {model_name}")
    
    try:
        # Load the model - using get_model from pretrained module
        device = "cuda" if th.cuda.is_available() else "cpu"
        logging.info(f"🔧 Using device: {device}")
        
        model = get_model(model_name)
        
        # Check max allowed segment for Transformer models
        max_allowed_segment = float('inf')
        if isinstance(model, HTDemucs):
            max_allowed_segment = float(model.segment)
        elif isinstance(model, BagOfModels):
            max_allowed_segment = model.max_allowed_segment
            logging.info(f"📦 Using bag of {len(model.models)} models for enhanced quality")
        
        # Move model to CPU and set to eval mode (as per Demucs documentation)
        model.cpu()
        model.eval()
        
        logging.info(f"Separated tracks will be stored in {output_path.resolve()}")
        logging.info(f"Separating track {input_path}")
        
        # Load the audio track
        wav = load_track(input_file, model.audio_channels, model.samplerate)
        
        # Normalize audio (as per Demucs main function)
        ref = wav.mean(0)
        wav -= ref.mean()
        wav /= ref.std()
        
        # Apply the model for separation with high-quality settings
        logging.info("🔄 Applying separation model...")
        sources = apply_model(
            model, 
            wav[None], 
            device=device,
            shifts=1,          # Number of random shifts (increase for better quality)
            split=True,        # Split audio in chunks to save memory
            overlap=0.25,      # Overlap between splits
            progress=True,     # Show progress
            num_workers=0,     # Number of parallel workers
            segment=None       # Auto-segment size
        )[0]
        
        # Denormalize (as per Demucs main function)
        sources *= ref.std()
        sources += ref.mean()
        
        # Prepare output format settings
        ext = "wav"  # Output format
        kwargs = {
            'samplerate': model.samplerate,
            'clip': 'rescale',        # Strategy for avoiding clipping
            'as_float': False,        # Use 16-bit instead of float32
            'bits_per_sample': 16,    # 16-bit audio
        }
        
        # Get the base filename without extension
        track_name = input_path.name.rsplit(".", 1)[0]
        
        # Save all stems using the Demucs filename format
        logging.info("💾 Saving separated stems...")
        stem_paths = {}
        
        for source, stem_name in zip(sources, model.sources):
            # Use Demucs filename format: {track}/{stem}.{ext}
            stem_file = output_path / f"{track_name}" / f"{stem_name}.{ext}"
            stem_file.parent.mkdir(parents=True, exist_ok=True)
            
            save_audio(source, str(stem_file), **kwargs)
            stem_paths[stem_name] = str(stem_file)
            logging.info(f"✅ Saved {stem_name}: {stem_file}")
        
        # Create accompaniment track (everything except vocals) if vocals exist
        if 'vocals' in model.sources:
            accompaniment = th.zeros_like(sources[0])
            for i, stem_name in enumerate(model.sources):
                if stem_name != 'vocals':
                    accompaniment += sources[i]
            
            accompaniment_file = output_path / f"{track_name}" / f"accompaniment.{ext}"
            save_audio(accompaniment, str(accompaniment_file), **kwargs)
            stem_paths['accompaniment'] = str(accompaniment_file)
            logging.info(f"✅ Saved accompaniment: {accompaniment_file}")
        
        logging.info(f"🎉 Stem separation completed successfully!")
        logging.info(f"📊 Available stems: {list(stem_paths.keys())}")
        
        return stem_paths
        
    except Exception as e:
        logging.error(f"❌ Stem separation failed: {str(e)}")
        raise

def separate_two_stems(input_file: str, output_dir: str, 
                      target_stem: str = "vocals", 
                      model_name: str = "htdemucs") -> dict:
    """
    Separate audio into target stem and everything else (two-stem separation)
    Based on Demucs --two-stems functionality
    
    Args:
        input_file: Path to input audio file
        output_dir: Directory to save separated stems
        target_stem: Stem to isolate (e.g., "vocals")
        model_name: Demucs model to use
    
    Returns:
        Dictionary with target_stem and no_{target_stem} paths
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file {input_file} does not exist")
    
    logging.info(f"🎵 Two-stem separation: isolating {target_stem}")
    
    try:
        device = "cuda" if th.cuda.is_available() else "cpu"
        model = get_model(model_name)
        model.cpu()
        model.eval()
        
        # Check if target stem is valid
        if target_stem not in model.sources:
            raise ValueError(f'Stem "{target_stem}" is not in selected model. '
                           f'Must be one of {", ".join(model.sources)}.')
        
        # Load and process audio
        wav = load_track(input_file, model.audio_channels, model.samplerate)
        ref = wav.mean(0)
        wav -= ref.mean()
        wav /= ref.std()
        
        # Apply model
        sources = apply_model(model, wav[None], device=device, 
                            shifts=1, split=True, overlap=0.25, 
                            progress=True, num_workers=0)[0]
        
        sources *= ref.std()
        sources += ref.mean()
        
        # Save configuration
        ext = "wav"
        kwargs = {
            'samplerate': model.samplerate,
            'clip': 'rescale',
            'as_float': False,
            'bits_per_sample': 16,
        }
        
        track_name = input_path.name.rsplit(".", 1)[0]
        stem_paths = {}
        
        # Extract target stem
        sources_list = list(sources)
        target_source = sources_list.pop(model.sources.index(target_stem))
        
        # Save target stem
        target_file = output_path / f"{track_name}" / f"{target_stem}.{ext}"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        save_audio(target_source, str(target_file), **kwargs)
        stem_paths[target_stem] = str(target_file)
        
        # Create and save the "no_{target_stem}" (everything else combined)
        other_stem = th.zeros_like(target_source)
        for source in sources_list:
            other_stem += source
        
        other_file = output_path / f"{track_name}" / f"no_{target_stem}.{ext}"
        save_audio(other_stem, str(other_file), **kwargs)
        stem_paths[f'no_{target_stem}'] = str(other_file)
        
        logging.info(f"✅ Two-stem separation completed: {target_stem} vs no_{target_stem}")
        return stem_paths
        
    except Exception as e:
        logging.error(f"❌ Two-stem separation failed: {str(e)}")
        raise

def get_available_models():
    """
    Get list of available Demucs models
    """
    return [
        "htdemucs",           # Default high-quality hybrid model
        "htdemucs_ft",        # Fine-tuned version  
        "htdemucs_6s",        # 6-stem version (includes piano, guitar)
        "mdx_extra",          # Extra high quality
        "mdx_extra_q",        # Quantized version (smaller, faster)
        "mdx",                # Standard MDX model
        "mdx_q",              # Quantized MDX
    ]

# Example usage and testing
if __name__ == "__main__":
    # Test the separation function
    logging.basicConfig(level=logging.INFO)
    
    # Example paths (update these for testing)
    test_input = "../../uploads/Ash Again  Gawr Gura x Casey Edwards.mp3"  # Path to your test audio file
    test_output = "../../uploads/tmp/demucs_test"

    try:
        # Test full separation
        print("Testing full stem separation...")
        stems = separate_stems(test_input, test_output, model_name="htdemucs")
        print(f"Full separation result: {stems}")
        
        # Test two-stem separation
        print("\nTesting two-stem separation...")
        two_stems = separate_two_stems(test_input, test_output + "_two_stem", 
                                     target_stem="vocals", model_name="htdemucs")
        print(f"Two-stem separation result: {two_stems}")
        
    except Exception as e:
        print(f"Test failed: {e}")