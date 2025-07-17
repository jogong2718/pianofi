import struct
import xml.etree.ElementTree as ET
from xml.dom import minidom

class MidiToMusicXML:
    def __init__(self):
        self.tracks = []
        self.ticks_per_quarter = 480
        self.tempo = 500000  # microseconds per quarter note (120 BPM)
        
    def read_variable_length(self, data, offset):
        """Read MIDI variable length quantity"""
        value = 0
        while True:
            byte = data[offset]
            offset += 1
            value = (value << 7) | (byte & 0x7F)
            if not (byte & 0x80):
                break
        return value, offset
    
    def parse_midi_file(self, filepath):
        """Parse MIDI file and extract note events"""
        with open(filepath, 'rb') as f:
            data = f.read()
        
        offset = 0
        
        # Parse header chunk
        if data[offset:offset+4] != b'MThd':
            raise ValueError("Not a valid MIDI file")
        offset += 4
        
        header_length = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4
        
        format_type, num_tracks, self.ticks_per_quarter = struct.unpack('>HHH', data[offset:offset+6])
        offset += 6
        
        # Parse tracks
        for track_num in range(num_tracks):
            if data[offset:offset+4] != b'MTrk':
                raise ValueError(f"Invalid track header at track {track_num}")
            offset += 4
            
            track_length = struct.unpack('>I', data[offset:offset+4])[0]
            offset += 4
            
            track_data = data[offset:offset+track_length]
            track_events = self.parse_track(track_data)
            self.tracks.append(track_events)
            offset += track_length
    
    def parse_track(self, track_data):
        """Parse individual track data"""
        events = []
        offset = 0
        running_status = 0
        current_time = 0
        
        while offset < len(track_data):
            # Read delta time
            delta_time, offset = self.read_variable_length(track_data, offset)
            current_time += delta_time
            
            # Read event
            event_byte = track_data[offset]
            
            if event_byte & 0x80:  # Status byte
                status = event_byte
                offset += 1
                running_status = status
            else:  # Data byte, use running status
                status = running_status
            
            if status == 0xFF:  # Meta event
                meta_type = track_data[offset]
                offset += 1
                length, offset = self.read_variable_length(track_data, offset)
                
                if meta_type == 0x51:  # Set tempo
                    self.tempo = struct.unpack('>I', b'\x00' + track_data[offset:offset+3])[0]
                
                offset += length
                
            elif (status & 0xF0) == 0x90:  # Note on
                note = track_data[offset]
                velocity = track_data[offset + 1]
                offset += 2
                
                if velocity > 0:
                    events.append({
                        'type': 'note_on',
                        'time': current_time,
                        'note': note,
                        'velocity': velocity,
                        'channel': status & 0x0F
                    })
                else:  # Velocity 0 = note off
                    events.append({
                        'type': 'note_off',
                        'time': current_time,
                        'note': note,
                        'channel': status & 0x0F
                    })
                    
            elif (status & 0xF0) == 0x80:  # Note off
                note = track_data[offset]
                velocity = track_data[offset + 1]
                offset += 2
                
                events.append({
                    'type': 'note_off',
                    'time': current_time,
                    'note': note,
                    'channel': status & 0x0F
                })
                
            else:
                # Skip other events
                if (status & 0xF0) in [0xA0, 0xB0, 0xE0]:  # 2-byte events
                    offset += 2
                elif (status & 0xF0) in [0xC0, 0xD0]:  # 1-byte events
                    offset += 1
                elif status == 0xF0:  # SysEx
                    length, offset = self.read_variable_length(track_data, offset)
                    offset += length
        
        return events
    
    def ticks_to_duration(self, ticks):
        """Convert MIDI ticks to note duration"""
        quarter_note_ticks = self.ticks_per_quarter
        
        # More granular duration detection
        if ticks >= quarter_note_ticks * 2:
            return 'half', 1
        elif ticks >= quarter_note_ticks:
            return 'quarter', 1
        elif ticks >= quarter_note_ticks // 2:
            return 'eighth', 1
        elif ticks >= quarter_note_ticks // 4:
            return '16th', 1
        elif ticks >= quarter_note_ticks // 8:
            return '32nd', 1
        else:
            return '64th', 1

    def midi_note_to_pitch(self, midi_note):
        """Convert MIDI note number to pitch notation"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_note // 12) - 1
        note = note_names[midi_note % 12]
        
        if '#' in note:
            step = note[0]
            alter = 1
        else:
            step = note
            alter = 0
            
        return step, alter, octave
    
    def insert_rests(self, chords):
        """Insert rests between chords where there are gaps"""
        if not chords:
            return chords
            
        result = []
        current_time = 0
        
        for chord in chords:
            chord_start = chord[0]['start_time']
            
            # Check if there's a gap before this chord
            if chord_start > current_time:
                rest_duration = chord_start - current_time
                # Split large rests into smaller ones if needed
                while rest_duration > 0:
                    rest_size = min(rest_duration, self.ticks_per_quarter * 2)  # Max half note rest
                    result.append({
                        'type': 'rest',
                        'start_time': current_time,
                        'duration_ticks': rest_size
                    })
                    current_time += rest_size
                    rest_duration -= rest_size
            
            # Add the chord
            result.append(chord)
            # Update current time to end of longest note in chord
            chord_end = max(note['start_time'] + note['duration_ticks'] for note in chord)
            current_time = chord_end
            
        return result

    def quantize_timing(self, ticks, grid_size=None):
        """Quantize timing to nearest musical division"""
        if grid_size is None:
            grid_size = self.ticks_per_quarter // 4  # Default to 16th note grid
        
        return round(ticks / grid_size) * grid_size
    
    def create_musicxml(self, output_filepath):
        """Generate MusicXML from parsed MIDI data"""
        # Combine all tracks and sort by time
        all_events = []
        for track in self.tracks:
            all_events.extend(track)
        all_events.sort(key=lambda x: x['time'])
        
        # Match note on/off events with correct timing
        active_notes = {}
        notes = []
        
        for event in all_events:
            if event['type'] == 'note_on':
                # Store note-on event with exact timing
                note_id = (event['note'], event['channel'])
                active_notes[note_id] = event
            elif event['type'] == 'note_off':
                note_id = (event['note'], event['channel'])
                if note_id in active_notes:
                    note_on = active_notes[note_id]
                    start_time = note_on['time']
                    end_time = event['time']
                    duration_ticks = end_time - start_time
                    
                    # Minimum duration check
                    if duration_ticks <= 0:
                        duration_ticks = self.ticks_per_quarter // 16  # Minimum duration
                    
                    notes.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration_ticks': duration_ticks,
                        'midi_note': event['note'],
                        'velocity': note_on['velocity'],
                        'channel': note_on['channel']
                    })
                    
                    del active_notes[note_id]
        
        # Handle any active notes that didn't receive a note-off
        for note_id, note_on in active_notes.items():
            # Set a reasonable duration for notes without a note-off
            duration_ticks = self.ticks_per_quarter
            notes.append({
                'start_time': note_on['time'],
                'end_time': note_on['time'] + duration_ticks,
                'duration_ticks': duration_ticks,
                'midi_note': note_id[0],
                'velocity': note_on['velocity'],
                'channel': note_on['channel']
            })
        
        # Sort by start time then by pitch for consistent ordering
        notes.sort(key=lambda x: (x['start_time'], x['midi_note']))
        
        # Find unique event times
        event_times = sorted(list(set([note['start_time'] for note in notes])))
        
        # Group notes by start time
        time_to_notes = {}
        for note in notes:
            start_time = note['start_time']
            if start_time not in time_to_notes:
                time_to_notes[start_time] = []
            time_to_notes[start_time].append(note)
        
        # Create events in time order
        events = []
        for time in event_times:
            if time in time_to_notes:
                events.append({
                    'type': 'chord',
                    'time': time,
                    'notes': sorted(time_to_notes[time], key=lambda x: x['midi_note'])
                })
        
        # Add rests between events
        musical_events = []
        if events:
            current_time = 0
            for event in events:
                event_time = event['time']
                
                if event_time > current_time:
                    # Add rest
                    rest_duration = event_time - current_time
                    musical_events.append({
                        'type': 'rest',
                        'time': current_time,
                        'duration_ticks': rest_duration
                    })
                
                musical_events.append(event)
                current_time = event_time
                
                # Don't advance current_time by note duration - we want events at their exact times
        
        # Generate MusicXML
        # Create XML structure
        root = ET.Element('score-partwise', version="3.1")
        
        # Part list
        part_list = ET.SubElement(root, 'part-list')
        score_part = ET.SubElement(part_list, 'score-part', id="P1")
        part_name = ET.SubElement(score_part, 'part-name')
        part_name.text = "Piano"
        
        # Part
        part = ET.SubElement(root, 'part', id="P1")
        
        # Measure 1
        measure = ET.SubElement(part, 'measure', number="1")
        
        # Attributes
        attributes = ET.SubElement(measure, 'attributes')
        divisions = ET.SubElement(attributes, 'divisions')
        divisions.text = str(self.ticks_per_quarter)
        
        key = ET.SubElement(attributes, 'key')
        fifths = ET.SubElement(key, 'fifths')
        fifths.text = "0"
        
        time_sig = ET.SubElement(attributes, 'time')
        beats = ET.SubElement(time_sig, 'beats')
        beats.text = "4"
        beat_type = ET.SubElement(time_sig, 'beat-type')
        beat_type.text = "4"
        
        clef = ET.SubElement(attributes, 'clef')
        sign = ET.SubElement(clef, 'sign')
        sign.text = "G"
        line = ET.SubElement(clef, 'line')
        line.text = "2"
        
        # Add bass clef for left hand
        staves = ET.SubElement(attributes, 'staves')
        staves.text = "2"
        
        clef2 = ET.SubElement(attributes, 'clef', number="2")
        sign2 = ET.SubElement(clef2, 'sign')
        sign2.text = "F"
        line2 = ET.SubElement(clef2, 'line')
        line2.text = "4"
        
        # Process musical events and create measures
        current_measure_time = 0
        measure_length = self.ticks_per_quarter * 4  # 4/4 time
        measure_num = 1
        
        # Track notes active in current measure
        active_notes = {}
        pending_tie_ends = {}
        
        # Create a timeline of all note-on and note-off events
        timeline_events = []
        for event in musical_events:
            if event['type'] == 'chord':
                for note in event['notes']:
                    # Add note-on event
                    timeline_events.append({
                        'type': 'note_start',
                        'time': note['start_time'],
                        'note': note
                    })
                    # Add note-off event
                    timeline_events.append({
                        'type': 'note_end',
                        'time': note['end_time'],
                        'note': note
                    })
            elif event['type'] == 'rest':
                timeline_events.append({
                    'type': 'rest',
                    'time': event['time'],
                    'duration_ticks': event['duration_ticks']
                })
        
        # Sort timeline by time
        timeline_events.sort(key=lambda x: x['time'])
        
        # Track currently active notes and voice assignments
        active_notes_by_measure = {}
        voice_assignments = {}
        current_voice = 1
        
        # Process timeline events
        for event in timeline_events:
            event_time = event['time']
            
            # Check if we need a new measure
            while event_time >= current_measure_time + measure_length:
                # Process measure boundary
                for midi_note, note_data in list(active_notes.items()):
                    # Calculate remaining duration to measure end
                    remaining = current_measure_time + measure_length - note_data['start_time']
                    
                    # Modify the note to end at measure boundary
                    note_data['duration_ticks'] = remaining
                    note_data['tied_to_next'] = True
                    
                    # Remember to start a tied note in the next measure
                    pending_tie_ends[midi_note] = {
                        'original_end': note_data['end_time'],
                        'next_measure_time': current_measure_time + measure_length
                    }
                
                # Create a new measure
                current_measure_time += measure_length
                measure_num += 1
                measure = ET.SubElement(part, 'measure', number=str(measure_num))
                
                # Add pending tied notes from previous measure
                for midi_note, tie_data in list(pending_tie_ends.items()):
                    # Calculate new duration
                    next_start = tie_data['next_measure_time']
                    new_duration = tie_data['original_end'] - next_start
                    
                    if new_duration > 0:
                        # Create tied note
                        note_elem = ET.SubElement(measure, 'note')
                        pitch = ET.SubElement(note_elem, 'pitch')
                        step, alter, octave = self.midi_note_to_pitch(midi_note)
                        
                        step_elem = ET.SubElement(pitch, 'step')
                        step_elem.text = step
                        
                        if alter != 0:
                            alter_elem = ET.SubElement(pitch, 'alter')
                            alter_elem.text = str(alter)
                        
                        octave_elem = ET.SubElement(pitch, 'octave')
                        octave_elem.text = str(octave)
                        
                        # Duration limited to measure end if needed
                        actual_duration = min(new_duration, measure_length)
                        duration_elem = ET.SubElement(note_elem, 'duration')
                        duration_elem.text = str(actual_duration)
                        
                        # Add tie notation
                        tie_elem = ET.SubElement(note_elem, 'tie', type="start")
                        
                        # Add notation elements
                        notations = ET.SubElement(note_elem, 'notations')
                        tied = ET.SubElement(notations, 'tied', type="start")
                        
                        # Update for potential continuation to next measure
                        if actual_duration < new_duration:
                            pending_tie_ends[midi_note] = {
                                'original_end': tie_data['original_end'],
                                'next_measure_time': next_start + actual_duration
                            }
                        else:
                            del pending_tie_ends[midi_note]
                    else:
                        del pending_tie_ends[midi_note]
            
            # Process the current event
            if event['type'] == 'rest':
                # Create rest - handle measure boundary crossing
                rest_duration = event['duration_ticks']
                remaining_in_measure = (current_measure_time + measure_length) - event_time
                
                if rest_duration > remaining_in_measure:
                    # Split rest across measures
                    if remaining_in_measure > 0:
                        # Add partial rest to current measure
                        note_elem = ET.SubElement(measure, 'note')
                        rest_elem = ET.SubElement(note_elem, 'rest')
                        duration = ET.SubElement(note_elem, 'duration')
                        duration.text = str(remaining_in_measure)
                        note_type, _ = self.ticks_to_duration(remaining_in_measure)
                        type_elem = ET.SubElement(note_elem, 'type')
                        type_elem.text = note_type
                    
                    # Continue with next measure handling in the next iteration
                else:
                    # Rest fits in current measure
                    note_elem = ET.SubElement(measure, 'note')
                    rest_elem = ET.SubElement(note_elem, 'rest')
                    duration = ET.SubElement(note_elem, 'duration')
                    duration.text = str(rest_duration)
                    note_type, _ = self.ticks_to_duration(rest_duration)
                    type_elem = ET.SubElement(note_elem, 'type')
                    type_elem.text = note_type
            
            elif event['type'] == 'chord':
                # Handle chord
                chord_notes = event['notes']
                
                # Process each note in the chord
                for i, note_data in enumerate(chord_notes):
                    midi_note = note_data['midi_note']
                    start_time = note_data['start_time']
                    end_time = note_data['end_time']
                    duration_ticks = note_data['duration_ticks']
                    
                    # Check if note crosses measure boundary
                    if start_time + duration_ticks > current_measure_time + measure_length:
                        # Adjust duration to fit in current measure
                        note_data['duration_ticks'] = (current_measure_time + measure_length) - start_time
                        note_data['tied_to_next'] = True
                        
                        # Remember to start a tied note in the next measure
                        pending_tie_ends[midi_note] = {
                            'original_end': end_time,
                            'next_measure_time': current_measure_time + measure_length
                        }
                    
                    # Create note element
                    note_elem = ET.SubElement(measure, 'note')
                    
                    # Add chord element for all notes except the first
                    if i > 0:
                        chord_elem = ET.SubElement(note_elem, 'chord')
                    
                    # Pitch
                    pitch = ET.SubElement(note_elem, 'pitch')
                    step, alter, octave = self.midi_note_to_pitch(midi_note)
                    
                    step_elem = ET.SubElement(pitch, 'step')
                    step_elem.text = step
                    
                    if alter != 0:
                        alter_elem = ET.SubElement(pitch, 'alter')
                        alter_elem.text = str(alter)
                    
                    octave_elem = ET.SubElement(pitch, 'octave')
                    octave_elem.text = str(octave)
                    
                    # Duration
                    duration = ET.SubElement(note_elem, 'duration')
                    duration.text = str(note_data['duration_ticks'])
                    
                    # Type
                    note_type, _ = self.ticks_to_duration(note_data['duration_ticks'])
                    type_elem = ET.SubElement(note_elem, 'type')
                    type_elem.text = note_type
                    
                    # Add ties if needed
                    if note_data.get('tied_to_previous', False):
                        tie_elem = ET.SubElement(note_elem, 'tie', type="stop")
                        notations = ET.SubElement(note_elem, 'notations')
                        tied = ET.SubElement(notations, 'tied', type="stop")
                    
                    if note_data.get('tied_to_next', False):
                        tie_elem = ET.SubElement(note_elem, 'tie', type="start")
                        notations = ET.SubElement(note_elem, 'notations')
                        tied = ET.SubElement(notations, 'tied', type="start")
                    
                    # Track active notes
                    if end_time > event_time + note_data['duration_ticks']:
                        active_notes[midi_note] = {
                            'start_time': start_time,
                            'end_time': end_time,
                            'duration_ticks': duration_ticks
                        }
                    else:
                        # Note ends within this event
                        if midi_note in active_notes:
                            del active_notes[midi_note]
        
        # Write to file
        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        # Remove empty lines
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

# Usage example
def convert_midi_to_musicxml(midi_file, output_file):
    converter = MidiToMusicXML()
    converter.parse_midi_file(midi_file)
    converter.create_musicxml(output_file)
    print(f"Converted {midi_file} to {output_file}")

# Example usage:
convert_midi_to_musicxml("09eded96-ed54-4aab-81f2-6fdb97d32afa.mid", "09eded96-ed54-4aab-81f2-6fdb97d32afa.musicxml")
