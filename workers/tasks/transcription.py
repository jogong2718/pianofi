import os
import sys
import torch as th
import torchaudio as ta
from pathlib import Path
import subprocess
import logging
import torch, torchaudio
from collections import Counter

from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH

try:
    from YourMT3.amt.src.model.init_train import initialize_trainer, update_config
    from YourMT3.amt.src.utils.task_manager import TaskManager
    from YourMT3.amt.src.config.vocabulary import drum_vocab_presets
    from YourMT3.amt.src.utils.utils import str2bool, Timer, write_model_output_as_midi
    from YourMT3.amt.src.utils.audio import slice_padded_array
    from YourMT3.amt.src.utils.note2event import mix_notes
    from YourMT3.amt.src.utils.event2note import merge_zipped_note_events_and_ties_to_notes
    from YourMT3.amt.src.model.ymt3 import YourMT3


    HAS_YOURMT3 = True
    logging.info("✅ YourMT3 available for accompaniment transcription")

except ImportError as e:
    HAS_YOURMT3 = False
    logging.warning("❌ YourMT3 not available, falling back to Basic Pitch for accompaniment transcription")
    logging.debug(f"YourMT3 import error: {e}")

# Global model cache
_yourmt3_model = None

def _load_yourmt3_model():
    """Load YourMT3 model (internal function)"""
    global _yourmt3_model
    
    if _yourmt3_model is not None:
        return _yourmt3_model
    
    if not HAS_YOURMT3:
        raise ImportError("YourMT3 not available")
    
    logging.info("🔄 Loading YourMT3 model...")
    
    # Set PyTorch precision
    if torch.__version__ >= "1.13":
        torch.set_float32_matmul_precision("high")
    
    # Create minimal args
    class Args:
        def __init__(self):
            self.exp_id = 'ymt3'
            self.project = 'ymt3'
            self.task = 'mt3_full_plus'
            self.eval_subtask_key = 'default'
            self.write_model_output = True
            self.debug_mode = False
            self.epochs = None
            self.task_cond_encoder = True
            self.task_cond_decoder = True
            self.pretrained = False
            self.base_name = "google/t5-v1_1-small"
    
    args = Args()
    
    # Initialize model
    _, _, dir_info, shared_cfg = initialize_trainer(args, stage='test')
    shared_cfg, audio_cfg, model_cfg = update_config(args, shared_cfg, stage='test')
    
    tm = TaskManager(
        task_name=args.task,
        max_shift_steps=int(shared_cfg["TOKENIZER"]["max_shift_steps"]),
        debug_mode=args.debug_mode
    )
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    model = YourMT3(
        audio_cfg=audio_cfg,
        model_cfg=model_cfg,
        shared_cfg=shared_cfg,
        optimizer=None,
        task_manager=tm,
        eval_subtask_key=args.eval_subtask_key,
        write_output_dir=None
    ).to(device)
    
    # Load checkpoint
    checkpoint_path = dir_info["last_ckpt_path"]
    checkpoint = torch.load(checkpoint_path, map_location=device)
    state_dict = checkpoint['state_dict']
    new_state_dict = {k: v for k, v in state_dict.items() if 'pitchshift' not in k}
    model.load_state_dict(new_state_dict, strict=False)
    
    _yourmt3_model = model.eval()
    logging.info("✅ YourMT3 model loaded")
    return _yourmt3_model

def transcribe_vocals(vocals_audio_path: str, output_midi_path: str):
    """
    Transcribe vocals using Basic Pitch and save as MIDI
    """
    logging.info(f"🎤 Transcribing vocals: {vocals_audio_path}")
    
    try:
        # Use Basic Pitch for vocals
        model_output, midi_data, note_events = predict(
            audio_path=vocals_audio_path,
            model_or_model_path=ICASSP_2022_MODEL_PATH
        )
        
        # Save MIDI
        midi_data.write(output_midi_path)
        logging.info(f"✅ Vocals saved: {output_midi_path}")
        return output_midi_path
        
    except Exception as e:
        logging.error(f"❌ Vocal transcription failed: {e}")
        # Create simple placeholder
        Path(output_midi_path).touch()
        return output_midi_path

def transcribe_accompaniment(accompaniment_audio_path: str, output_midi_path: str):
    """
    Transcribe accompaniment using YourMT3 (with Basic Pitch fallback)
    """
    logging.info(f"🎹 Transcribing accompaniment: {accompaniment_audio_path}")
    
    # Try YourMT3 first
    if HAS_YOURMT3:
        try:
            model = _load_yourmt3_model()
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
            # Load and process audio
            audio, sr = torchaudio.load(accompaniment_audio_path)
            audio = torch.mean(audio, dim=0).unsqueeze(0)  # Convert to mono
            audio = torchaudio.functional.resample(audio, sr, model.audio_cfg['sample_rate'])
            
            # Slice audio
            audio_segments = slice_padded_array(
                audio, 
                model.audio_cfg['input_frames'], 
                model.audio_cfg['input_frames']
            )
            audio_segments = torch.from_numpy(audio_segments.astype('float32')).to(device).unsqueeze(1)
            
            # Inference
            pred_token_arr, _ = model.inference_file(bsz=8, audio_segments=audio_segments)
            
            # Post-process
            num_channels = model.task_manager.num_decoding_channels
            n_items = audio_segments.shape[0]
            start_secs_file = [
                model.audio_cfg['input_frames'] * i / model.audio_cfg['sample_rate'] 
                for i in range(n_items)
            ]
            
            pred_notes_in_file = []
            n_err_cnt = Counter()
            
            for ch in range(num_channels):
                pred_token_arr_ch = [arr[:, ch, :] for arr in pred_token_arr]
                zipped_note_events_and_tie, list_events, ne_err_cnt = model.task_manager.detokenize_list_batches(
                    pred_token_arr_ch, start_secs_file, return_events=True
                )
                pred_notes_ch, n_err_cnt_ch = merge_zipped_note_events_and_ties_to_notes(zipped_note_events_and_tie)
                pred_notes_in_file.append(pred_notes_ch)
                n_err_cnt += n_err_cnt_ch
            
            # Mix notes and save
            pred_notes = mix_notes(pred_notes_in_file)
            
            output_dir = Path(output_midi_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            write_model_output_as_midi(
                pred_notes, 
                str(output_dir),
                Path(output_midi_path).stem, 
                model.midi_output_inverse_vocab
            )
            
            # Move from model_output subdirectory
            generated_midi = output_dir / "model_output" / f"{Path(output_midi_path).stem}.mid"
            if generated_midi.exists():
                generated_midi.rename(output_midi_path)
                try:
                    generated_midi.parent.rmdir()
                except:
                    pass
            
            if Path(output_midi_path).exists():
                logging.info(f"✅ YourMT3 accompaniment saved: {output_midi_path}")
                return output_midi_path
                
        except Exception as e:
            logging.error(f"❌ YourMT3 failed: {e}")
    
    # Fallback to Basic Pitch
    try:
        logging.info("🔄 Using Basic Pitch fallback")
        model_output, midi_data, note_events = predict(
            audio_path=accompaniment_audio_path,
            model_or_model_path=ICASSP_2022_MODEL_PATH
        )
        midi_data.write(output_midi_path)
        logging.info(f"✅ Basic Pitch accompaniment saved: {output_midi_path}")
        return output_midi_path
        
    except Exception as e:
        logging.error(f"❌ All transcription methods failed: {e}")
        # Create simple placeholder
        Path(output_midi_path).touch()
        return output_midi_path
    
# Add this to the end of your transcription.py file

def main():
    """
    Test transcription functions with the demucs test files
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Test folder path
    test_folder = Path("/Users/jonathangong/Code/Repositories/pianofi-app/backend/uploads/tmp/demucs_test_two_stem/Ash Again  Gawr Gura x Casey Edwards")
    
    if not test_folder.exists():
        logging.error(f"❌ Test folder not found: {test_folder}")
        return
    
    logging.info(f"🧪 Testing transcription with files from: {test_folder}")
    
    # Input files
    vocals_file = test_folder / "vocals.wav"
    no_vocals_file = test_folder / "no_vocals.wav"  # This is the accompaniment
    
    # Output directory
    output_dir = test_folder / "transcriptions"
    output_dir.mkdir(exist_ok=True)
    
    # Output files
    vocals_output = output_dir / "vocals.mid"
    accompaniment_output = output_dir / "accompaniment.mid"
    
    # Check if input files exist
    if not vocals_file.exists():
        logging.error(f"❌ Vocals file not found: {vocals_file}")
        return
    
    if not no_vocals_file.exists():
        logging.error(f"❌ No vocals file not found: {no_vocals_file}")
        return
    
    logging.info(f"📁 Input files:")
    logging.info(f"  - Vocals: {vocals_file}")
    logging.info(f"  - Accompaniment: {no_vocals_file}")
    logging.info(f"📁 Output directory: {output_dir}")
    
    try:
        # Test vocals transcription
        logging.info("\n" + "="*50)
        logging.info("🎤 TESTING VOCALS TRANSCRIPTION")
        logging.info("="*50)
        
        vocals_result = transcribe_vocals(str(vocals_file), str(vocals_output))
        
        if Path(vocals_result).exists() and Path(vocals_result).stat().st_size > 0:
            logging.info(f"✅ Vocals transcription completed successfully!")
            logging.info(f"📄 Output: {vocals_result}")
        else:
            logging.warning(f"⚠️ Vocals transcription created empty file")
        
        # Test accompaniment transcription
        logging.info("\n" + "="*50)
        logging.info("🎹 TESTING ACCOMPANIMENT TRANSCRIPTION")
        logging.info("="*50)
        
        accompaniment_result = transcribe_accompaniment(str(no_vocals_file), str(accompaniment_output))
        
        if Path(accompaniment_result).exists() and Path(accompaniment_result).stat().st_size > 0:
            logging.info(f"✅ Accompaniment transcription completed successfully!")
            logging.info(f"📄 Output: {accompaniment_result}")
        else:
            logging.warning(f"⚠️ Accompaniment transcription created empty file")
        
        # Summary
        logging.info("\n" + "="*50)
        logging.info("📊 TRANSCRIPTION TEST SUMMARY")
        logging.info("="*50)
        
        logging.info(f"Vocals file: {vocals_file.name}")
        logging.info(f"  → Result: {'✅ Success' if Path(vocals_result).stat().st_size > 0 else '⚠️ Empty'}")
        logging.info(f"  → Size: {Path(vocals_result).stat().st_size} bytes")
        
        logging.info(f"Accompaniment file: {no_vocals_file.name}")
        logging.info(f"  → Result: {'✅ Success' if Path(accompaniment_result).stat().st_size > 0 else '⚠️ Empty'}")
        logging.info(f"  → Size: {Path(accompaniment_result).stat().st_size} bytes")
        
        logging.info(f"\n📁 All outputs saved to: {output_dir}")
        
        # List output files
        output_files = list(output_dir.glob("*.mid"))
        if output_files:
            logging.info("📄 Generated MIDI files:")
            for file in output_files:
                logging.info(f"  - {file.name} ({file.stat().st_size} bytes)")
        
    except Exception as e:
        logging.error(f"❌ Test failed with error: {e}")
        import traceback
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    main()