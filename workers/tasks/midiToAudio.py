import logging
import os
import struct
import json
from pathlib import Path
import subprocess
from midi2audio import FluidSynth

logging.basicConfig(level=logging.INFO)

class MidiToAudio:
    def __init__(self):
        self.ticks_per_quarter = 480
        self.tempo_changes = []
        self.time_signature_changes = []
        self.measures = {}
        self.total_duration = 0

    
    def process_midi_file(self, midi_file, job_id):
        try:
            logging.info(f"Processing MIDI file: {midi_file} for job {job_id}")
            
            self._parse_midi_timing(midi_file)
            self._calculate_measures()
            
            metadata = self._create_metadata()
            logging.info(f"Generated metadata for {metadata['total_measures']} measures")
            
            return metadata
            
        except Exception as e:
            logging.error(f"Error processing MIDI file: {e}")
            raise e

    def _parse_midi_timing(self, midi_file_path):
        """
        Parse MIDI file to extract timing information
        Reuses logic from midiToXml.py but focuses on timing data
        """
        logging.info("Parsing MIDI timing information...")
        
        with open(midi_file_path, 'rb') as f:
            data = f.read()
        
        # Read MIDI header to get ticks per quarter
        offset = 8
        _, _, self.ticks_per_quarter = struct.unpack('>HHH', data[offset:offset+6])
        offset = 14
        
        logging.info(f"MIDI timing resolution: {self.ticks_per_quarter} ticks per quarter note")
        
        # Initialize with defaults
        self.tempo_changes = [{'tick': 0, 'tempo': 500000, 'bpm': 120.0}]
        self.time_signature_changes = [{'tick': 0, 'numerator': 4, 'denominator': 4}]
        
        # Parse all tracks for timing events
        while offset < len(data):
            if data[offset:offset+4] == b'MTrk':
                offset += 8 
                offset = self._parse_track_timing(data, offset)
            else:
                offset += 1
        
        logging.info(f"Found {len(self.tempo_changes)} tempo changes")
        logging.info(f"Found {len(self.time_signature_changes)} time signature changes")


    def _parse_track_timing(self, data, offset):
        """
        Parse single track looking for timing events only
        Based on midiToXml.py but focused on tempo and time signature changes
        """
        track_end = offset + struct.unpack('>I', data[offset-4:offset])[0]
        current_time = 0
        running_status = 0
        
        while offset < track_end:
            # Read delta time
            delta_time, offset = self._read_varint(data, offset)
            current_time += delta_time
            
            # Read event
            if data[offset] & 0x80:
                running_status = data[offset]
                offset += 1
            
            status = running_status & 0xF0
            
            # Skip note events, we only care about timing meta events
            if status == 0x90:  # Note on
                offset += 2
            elif status == 0x80:  # Note off  
                offset += 2
            elif status in [0xA0, 0xB0, 0xE0]:  # 2-byte events
                offset += 2
            elif status in [0xC0, 0xD0]:  # 1-byte events
                offset += 1
            elif data[offset-1] == 0xFF:  # Meta event - THIS IS WHAT WE WANT
                meta_type = data[offset]
                offset += 1
                length, offset = self._read_varint(data, offset)
                
                if meta_type == 0x51 and length == 3:
                    # Set Tempo event (microseconds per quarter note)
                    tempo_bytes = data[offset:offset+3]
                    microseconds_per_quarter = int.from_bytes(tempo_bytes, byteorder='big')
                    bpm = round(60000000 / microseconds_per_quarter, 2)
                    
                    self.tempo_changes.append({
                        'tick': current_time,
                        'tempo': microseconds_per_quarter,
                        'bpm': bpm
                    })
                    logging.info(f"Found tempo change at tick {current_time}: {bpm} BPM")
                    
                elif meta_type == 0x58 and length == 4:
                    # Time Signature event
                    numerator = data[offset]
                    denominator = 2 ** data[offset + 1]  # Stored as power of 2
                    
                    self.time_signature_changes.append({
                        'tick': current_time,
                        'numerator': numerator,
                        'denominator': denominator
                    })
                    logging.info(f"Found time signature at tick {current_time}: {numerator}/{denominator}")
                
                offset += length
            else:
                offset += 1
                
        return offset

    def _read_varint(self, data, offset):
        """Read MIDI variable length integer"""
        value = 0
        while True:
            byte = data[offset]
            offset += 1
            value = (value << 7) | (byte & 0x7F)
            if not (byte & 0x80):
                break
        return value, offset
    
    def _ticks_to_seconds(self, target_tick):
        """Convert MIDI ticks to real seconds using tempo changes"""
        seconds = 0.0
        current_tick = 0
        
        for i, tempo_change in enumerate(self.tempo_changes):
            next_tempo_tick = self.tempo_changes[i + 1]['tick'] if i + 1 < len(self.tempo_changes) else target_tick
            
            if target_tick <= tempo_change['tick']:
                break
                
            tick_range_end = min(next_tempo_tick, target_tick)
            ticks_in_range = tick_range_end - current_tick
            
            if ticks_in_range > 0:
                microseconds_per_quarter = tempo_change['tempo']
                seconds_per_tick = microseconds_per_quarter / (1000000 * self.ticks_per_quarter)
                seconds += ticks_in_range * seconds_per_tick
            
            current_tick = tick_range_end
            
        return round(seconds, 3)

    def _calculate_measures(self):
        """Calculate measure boundaries in seconds"""
        logging.info("Calculating measure boundaries...")
        
        # Find the last tick with any event
        last_tick = max([tc['tick'] for tc in self.tempo_changes] + 
                       [ts['tick'] for ts in self.time_signature_changes])
        
        current_tick = 0
        measure_num = 1
        current_time_sig = self.time_signature_changes[0]
        time_sig_index = 0
        
        while current_tick < last_tick:
            # Check for time signature changes
            while (time_sig_index + 1 < len(self.time_signature_changes) and 
                   self.time_signature_changes[time_sig_index + 1]['tick'] <= current_tick):
                time_sig_index += 1
                current_time_sig = self.time_signature_changes[time_sig_index]
            
            # Calculate ticks per measure
            beats_per_measure = current_time_sig['numerator']
            beat_unit = current_time_sig['denominator']
            quarter_notes_per_measure = beats_per_measure * (4 / beat_unit)
            ticks_per_measure = int(quarter_notes_per_measure * self.ticks_per_quarter)
            
            measure_start_tick = current_tick
            measure_end_tick = current_tick + ticks_per_measure
            
            # Convert to seconds
            start_seconds = self._ticks_to_seconds(measure_start_tick)
            end_seconds = self._ticks_to_seconds(measure_end_tick)
            
            self.measures[measure_num] = {
                'start_tick': measure_start_tick,
                'end_tick': measure_end_tick,
                'start_seconds': start_seconds,
                'end_seconds': end_seconds,
                'duration': round(end_seconds - start_seconds, 3)
            }
            
            current_tick = measure_end_tick
            measure_num += 1
            
            # Safety check
            if measure_num > 1000:
                logging.warning("Stopping at 1000 measures to prevent infinite loop")
                break
        
        self.total_duration = self._ticks_to_seconds(last_tick)
        logging.info(f"Calculated {len(self.measures)} measures, total duration: {self.total_duration:.2f} seconds")

    def _create_metadata(self):
        """Create measure timing metadata for frontend"""
        return {
            'total_duration': self.total_duration,
            'total_measures': len(self.measures),
            'ticks_per_quarter': self.ticks_per_quarter,
            'measures': {
                str(measure_num): {
                    'start': data['start_seconds'],
                    'end': data['end_seconds'],
                    'duration': data['duration']
                }
                for measure_num, data in self.measures.items()
            }
        }

    def _synthesize_audio(self, midi_file_path, output_file, job_id):
        """Generate audio using midi2audio library with explicit soundfont"""
        
        audio_file = output_file
        audio_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Try to find a soundfont
        soundfont_paths = [
            "./FluidR3_GM.sf2",  # Downloaded file
            "./FluidR3_GM.sf3", 
            "./Piano.sf2",
            "/usr/share/soundfonts/FluidR3_GM.sf2",
            "/opt/homebrew/share/soundfonts/FluidR3_GM.sf2"
        ]
        
        soundfont = None
        for path in soundfont_paths:
            if Path(path).exists():
                soundfont = path
                break
        
        try:
            if soundfont:
                logging.info(f"Using soundfont: {soundfont}")
                fs = FluidSynth(sound_font=soundfont)
            else:
                logging.warning("No soundfont found, using default (may be silent)")
                fs = FluidSynth()
            
            fs.midi_to_audio(str(midi_file_path), str(audio_file))
            
            logging.info(f"Audio synthesis complete: {audio_file}")
            return str(audio_file)
            
        except Exception as e:
            logging.error(f"MIDI to audio conversion failed: {e}")
            raise Exception(f"MIDI to audio conversion failed: {e}")

def convert_midi_to_audio(midi_file, output_file, job_id):
    converter = MidiToAudio()
    
    metadata = converter.process_midi_file(midi_file, job_id)

    audio_path = converter._synthesize_audio(midi_file, output_file, job_id)
    
    return audio_path, metadata

if __name__ == "__main__":
    job_id = "09eded96-ed54-4aab-81f2-6fdb97d32afa"
    midi_file = Path(f"uploads/{job_id}.mid")
    output_file = Path(f"uploads/{job_id}.wav")
    
    metadata = convert_midi_to_audio(midi_file, output_file, job_id)