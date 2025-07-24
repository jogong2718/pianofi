import logging
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import defaultdict

class MidiToMusicXML:
    def __init__(self):
        self.ticks_per_quarter = 480
        self.notes = []
        
    def parse_midi_file(self, filepath):
        """Parse MIDI file and extract notes"""
        with open(filepath, 'rb') as f:
            data = f.read()
        
        # Skip header and get timing
        offset = 8
        _, _, self.ticks_per_quarter = struct.unpack('>HHH', data[offset:offset+6])
        offset = 14
        
        # Parse all tracks
        while offset < len(data):
            if data[offset:offset+4] == b'MTrk':
                offset += 8  # Skip MTrk and length
                offset = self._parse_track(data, offset)
            else:
                offset += 1
    
    def _parse_track(self, data, offset):
        """Parse single track"""
        track_end = offset + struct.unpack('>I', data[offset-4:offset])[0]
        current_time = 0
        running_status = 0
        note_ons = {}
        
        while offset < track_end:
            # Read delta time
            delta_time, offset = self._read_varint(data, offset)
            current_time += delta_time
            
            # Read event
            if data[offset] & 0x80:
                running_status = data[offset]
                offset += 1
            
            status = running_status & 0xF0
            
            if status == 0x90:  # Note on
                note, velocity = data[offset:offset+2]
                offset += 2
                if velocity > 0:
                    note_ons[note] = current_time
                else:  # Velocity 0 = note off
                    if note in note_ons:
                        self._add_note(note, note_ons[note], current_time)
                        del note_ons[note]
                        
            elif status == 0x80:  # Note off
                note = data[offset]
                offset += 2
                if note in note_ons:
                    self._add_note(note, note_ons[note], current_time)
                    del note_ons[note]
                    
            elif status in [0xA0, 0xB0, 0xE0]:  # 2-byte events
                offset += 2
            elif status in [0xC0, 0xD0]:  # 1-byte events
                offset += 1
            elif data[offset-1] == 0xFF:  # Meta event
                offset += 1
                length, offset = self._read_varint(data, offset)
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
    
    def _add_note(self, midi_note, start_time, end_time):
        """Add note to collection"""
        duration = max(end_time - start_time, self.ticks_per_quarter // 16)
        self.notes.append({
            'midi_note': midi_note,
            'start_time': start_time,
            'duration': duration,
            'pitch': self._midi_to_pitch(midi_note)
        })
    
    def _midi_to_pitch(self, midi_note):
        """Convert MIDI note to pitch info"""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_note // 12) - 1
        note_name = notes[midi_note % 12]
        
        if '#' in note_name:
            return {'step': note_name[0], 'alter': 1, 'octave': octave}
        else:
            return {'step': note_name, 'alter': 0, 'octave': octave}
    
    def _quantize_time(self, time):
        """Quantize time to nearest 32nd note"""
        grid = self.ticks_per_quarter // 16  # important
        return round(time / grid) * grid
    
    def _get_note_type(self, duration):
        """Get note type from duration"""
        quarter = self.ticks_per_quarter
        if duration >= quarter * 2:
            return 'half'
        elif duration >= quarter:
            return 'quarter'
        elif duration >= quarter // 2:
            return 'eighth'
        elif duration >= quarter // 4:
            return '16th'
        else:
            return '32nd'
    
    def _add_chord_with_duration(self, measure, chord_notes, duration, beam_state=None):
        """Add chord to measure with specific duration"""
        # Sort notes by pitch (lowest first)
        chord_notes.sort(key=lambda x: x['midi_note'])
        
        for i, note in enumerate(chord_notes):
            note_elem = ET.SubElement(measure, 'note')
            
            # Add chord element for all notes except first
            if i > 0:
                chord = ET.SubElement(note_elem, 'chord')
            
            # Pitch
            pitch = ET.SubElement(note_elem, 'pitch')
            step = ET.SubElement(pitch, 'step')
            step.text = note['pitch']['step']
            
            if note['pitch']['alter'] != 0:
                alter = ET.SubElement(pitch, 'alter')
                alter.text = str(note['pitch']['alter'])
            
            octave = ET.SubElement(pitch, 'octave')
            octave.text = str(note['pitch']['octave'])
            
            # Duration
            duration_elem = ET.SubElement(note_elem, 'duration')
            duration_elem.text = str(duration)
            
            # Type
            note_type = ET.SubElement(note_elem, 'type')
            note_type.text = self._get_note_type(duration)
            
            # Add beam information if applicable and it's the first note in the chord
            if beam_state and i == 0 and self._should_beam(duration):
                beam = ET.SubElement(note_elem, 'beam', number="1")
                beam.text = beam_state

    def _should_beam(self, duration):
        """Determine if a note should be beamed based on its duration"""
        # Notes that can be beamed: eighth notes and shorter
        note_type = self._get_note_type(duration)
        return note_type in ['eighth', '16th', '32nd']
    
    def create_musicxml(self, output_filepath):
        """Generate MusicXML"""
        if not self.notes:
            return
            
        # Quantize all notes
        for note in self.notes:
            note['start_time'] = self._quantize_time(note['start_time'])
            note['duration'] = max(self._quantize_time(note['duration']), 
                                 self.ticks_per_quarter // 16)

        # Sort notes by start time
        self.notes.sort(key=lambda x: x['start_time'])
        
        # Create timeline of chord start events only
        chord_starts = defaultdict(list)
        for note in self.notes:
            chord_starts[note['start_time']].append(note)
        
        # Create musical moments based on chord starts
        musical_moments = []
        chord_times = sorted(chord_starts.keys())
        
        for i, chord_time in enumerate(chord_times):
            chord_notes = chord_starts[chord_time]
            
            # Determine duration until next chord or end of longest note
            if i + 1 < len(chord_times):
                next_chord_time = chord_times[i + 1]
                # Duration is until next chord starts
                duration = next_chord_time - chord_time
            else:
                # Last chord - duration is length of longest note
                duration = max(note['duration'] for note in chord_notes)
            
            musical_moments.append({
                'time': chord_time,
                'duration': duration,
                'notes': chord_notes
            })
        
        # Create XML structure
        root = ET.Element('score-partwise', version="3.1")
        
        # Part list
        part_list = ET.SubElement(root, 'part-list')
        
        # Treble part
        score_part1 = ET.SubElement(part_list, 'score-part', id="P1")
        part_name1 = ET.SubElement(score_part1, 'part-name')
        part_name1.text = "Treble"
        
        # Bass part
        score_part2 = ET.SubElement(part_list, 'score-part', id="P2")
        part_name2 = ET.SubElement(score_part2, 'part-name')
        part_name2.text = "Bass"
        
        # Treble part
        treble_part = ET.SubElement(root, 'part', id="P1")
        
        # Bass part
        bass_part = ET.SubElement(root, 'part', id="P2")
        
        # Generate measures
        measure_length = self.ticks_per_quarter * 4  # 4/4 time
        current_time = 0
        measure_num = 1
        moment_index = 0
        
        while moment_index < len(musical_moments):
            treble_measure = ET.SubElement(treble_part, 'measure', number=str(measure_num))
            bass_measure = ET.SubElement(bass_part, 'measure', number=str(measure_num))
            measure_end = current_time + measure_length
            
            # Add attributes to first measure
            if measure_num == 1:
                self._add_measure_attributes(treble_measure, "treble")
                self._add_measure_attributes(bass_measure, "bass")
            
            # Track beaming state
            treble_beam_active = False
            bass_beam_active = False
            last_treble_duration = 0
            last_bass_duration = 0
            
            # Track last rest elements in each part
            last_treble_rest = None
            last_bass_rest = None
            
            # Add musical moments in this measure
            while (moment_index < len(musical_moments) and 
                   musical_moments[moment_index]['time'] < measure_end):
                
                moment = musical_moments[moment_index]
                moment_time = moment['time']
                
                # Add rest if needed
                if moment_time > current_time:
                    rest_duration = moment_time - current_time
                    last_treble_rest = self._add_rest(treble_measure, rest_duration, last_treble_rest)
                    last_bass_rest = self._add_rest(bass_measure, rest_duration, last_bass_rest)
                    current_time = moment_time
                    # End any active beams when a rest is inserted
                    treble_beam_active = False
                    bass_beam_active = False
                
                # Calculate actual duration (clip to measure boundary)
                actual_duration = min(moment['duration'], measure_end - moment_time)
                
                # Split notes between treble and bass
                treble_notes = [note for note in moment['notes'] if note['midi_note'] >= 60]  # Middle C and above
                bass_notes = [note for note in moment['notes'] if note['midi_note'] < 60]  # Below middle C
                
                # Handle treble part
                if treble_notes:
                    # Notes - reset last rest since we're adding notes
                    last_treble_rest = None
                    
                    # Determine beam state for treble
                    treble_beam_state = None
                    if self._should_beam(actual_duration):
                        if treble_beam_active and actual_duration == last_treble_duration:
                            treble_beam_state = "continue"
                        else:
                            treble_beam_active = True
                            treble_beam_state = "begin"
                        
                        # Check if next moment should continue the beam
                        next_moment_idx = moment_index + 1
                        if (next_moment_idx >= len(musical_moments) or 
                            musical_moments[next_moment_idx]['time'] >= measure_end or
                            not self._should_beam(musical_moments[next_moment_idx]['duration']) or
                            musical_moments[next_moment_idx]['duration'] != actual_duration):
                            treble_beam_state = "end"
                            treble_beam_active = False
                    
                    self._add_chord_with_duration(treble_measure, treble_notes, actual_duration, treble_beam_state)
                    last_treble_duration = actual_duration
                else:
                    # Rest - maintain consecutive rest tracking
                    last_treble_rest = self._add_rest(treble_measure, actual_duration, last_treble_rest)
                    treble_beam_active = False
                
                # Handle bass part
                if bass_notes:
                    # Notes - reset last rest since we're adding notes
                    last_bass_rest = None
                    
                    # Determine beam state for bass
                    bass_beam_state = None
                    if self._should_beam(actual_duration):
                        if bass_beam_active and actual_duration == last_bass_duration:
                            bass_beam_state = "continue"
                        else:
                            bass_beam_active = True
                            bass_beam_state = "begin"
                        
                        # Check if next moment should continue the beam
                        next_moment_idx = moment_index + 1
                        if (next_moment_idx >= len(musical_moments) or 
                            musical_moments[next_moment_idx]['time'] >= measure_end or
                            not self._should_beam(musical_moments[next_moment_idx]['duration']) or
                            musical_moments[next_moment_idx]['duration'] != actual_duration):
                            bass_beam_state = "end"
                            bass_beam_active = False
                    
                    self._add_chord_with_duration(bass_measure, bass_notes, actual_duration, bass_beam_state)
                    last_bass_duration = actual_duration
                else:
                    # Rest - maintain consecutive rest tracking
                    last_bass_rest = self._add_rest(bass_measure, actual_duration, last_bass_rest)
                    bass_beam_active = False
                
                current_time = moment_time + actual_duration
                moment_index += 1
            
            # Fill rest of measure with rest if needed
            if current_time < measure_end:
                rest_duration = measure_end - current_time
                self._add_rest(treble_measure, rest_duration, last_treble_rest)
                self._add_rest(bass_measure, rest_duration, last_bass_rest)
            
            current_time = measure_end
            measure_num += 1
        
        # Write XML file
        self._write_xml(root, output_filepath)
    
    def _add_measure_attributes(self, measure, clef_type="treble"):
        """Add measure attributes (time signature, key, clef)"""
        attributes = ET.SubElement(measure, 'attributes')
        
        # Divisions
        divisions = ET.SubElement(attributes, 'divisions')
        divisions.text = str(self.ticks_per_quarter)
        
        # Key signature (C major)
        key = ET.SubElement(attributes, 'key')
        fifths = ET.SubElement(key, 'fifths')
        fifths.text = "0"
        
        # Time signature (4/4)
        time_sig = ET.SubElement(attributes, 'time')
        beats = ET.SubElement(time_sig, 'beats')
        beats.text = "4"
        beat_type = ET.SubElement(time_sig, 'beat-type')
        beat_type.text = "4"
        
        # Clef
        clef = ET.SubElement(attributes, 'clef')
        sign = ET.SubElement(clef, 'sign')
        line = ET.SubElement(clef, 'line')
        
        if clef_type == "treble":
            sign.text = "G"
            line.text = "2"
        else:  # bass
            sign.text = "F"
            line.text = "4"
    
    def _add_rest(self, measure, duration, previous_rest=None):
        """
        Add rest to measure or update an existing rest
        Returns the added/updated rest element
        """
        if previous_rest is not None:
            # Update existing rest instead of adding a new one
            prev_duration = int(previous_rest.find('duration').text)
            new_duration = prev_duration + duration
            
            # Update duration
            previous_rest.find('duration').text = str(new_duration)
            
            # Update note type
            previous_rest.find('type').text = self._get_note_type(new_duration)
            
            return previous_rest
        else:
            # Create a new rest
            note = ET.SubElement(measure, 'note')
            rest = ET.SubElement(note, 'rest')
            
            duration_elem = ET.SubElement(note, 'duration')
            duration_elem.text = str(duration)
            
            note_type = ET.SubElement(note, 'type')
            note_type.text = self._get_note_type(duration)
            
            return note
    
    def _add_chord(self, measure, chord_notes, measure_end):
        """Add chord to measure"""
        # Sort notes by pitch (lowest first)
        chord_notes.sort(key=lambda x: x['midi_note'])
        
        for i, note in enumerate(chord_notes):
            note_elem = ET.SubElement(measure, 'note')
            
            # Add chord element for all notes except first
            if i > 0:
                chord = ET.SubElement(note_elem, 'chord')
            
            # Pitch
            pitch = ET.SubElement(note_elem, 'pitch')
            step = ET.SubElement(pitch, 'step')
            step.text = note['pitch']['step']
            
            if note['pitch']['alter'] != 0:
                alter = ET.SubElement(pitch, 'alter')
                alter.text = str(note['pitch']['alter'])
            
            octave = ET.SubElement(pitch, 'octave')
            octave.text = str(note['pitch']['octave'])
            
            # Duration (clip to measure boundary)
            duration = min(note['duration'], 
                          measure_end - note['start_time'])
            
            duration_elem = ET.SubElement(note_elem, 'duration')
            duration_elem.text = str(duration)
            
            # Type
            note_type = ET.SubElement(note_elem, 'type')
            note_type.text = self._get_note_type(duration)
            
            # Add tie if note extends beyond measure
            if note['duration'] > duration:
                tie = ET.SubElement(note_elem, 'tie', type="start")
                notations = ET.SubElement(note_elem, 'notations')
                tied = ET.SubElement(notations, 'tied', type="start")
    
    def _write_xml(self, root, filepath):
        """Write XML to file with formatting"""
        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        # Remove empty lines
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

def convert_midi_to_musicxml(midi_file, output_file):
    """Convert MIDI file to MusicXML"""
    converter = MidiToMusicXML()
    converter.parse_midi_file(midi_file)
    converter.create_musicxml(output_file)
    print(f"Converted {midi_file} to {output_file}")

def convert_midi_to_xml(midi_file_path, output_path, job_id=None):
    """
    Convert MIDI file to MusicXML format
    
    Args:
        midi_file_path: Path to the input MIDI file
        output_path: Path where the XML file should be saved
        job_id: Optional job ID for logging
    
    Returns:
        str: Path to the generated XML file
        
    Raises:
        Exception: If conversion fails
    """
    try:
        if job_id:
            logging.info(f"Converting MIDI to MusicXML for job {job_id}")
        else:
            logging.info(f"Converting MIDI {midi_file_path} to MusicXML")
    
        convert_midi_to_musicxml(midi_file_path, output_path)
        
        # Verify the file was created
        if not Path(output_path).exists():
            raise Exception(f"XML file was not created at {output_path}")
            
        file_size = Path(output_path).stat().st_size
        logging.info(f"Successfully converted to XML: {output_path} ({file_size} bytes)")
        
        return output_path
        
    except Exception as e:
        error_msg = f"Error converting MIDI to MusicXML: {e}"
        if job_id:
            error_msg = f"Error converting MIDI to MusicXML for job {job_id}: {e}"
        logging.error(error_msg)
        raise