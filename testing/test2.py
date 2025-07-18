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
        """Quantize time to nearest 16th note"""
        grid = self.ticks_per_quarter // 4
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
    
    def create_musicxml(self, output_filepath):
        """Generate MusicXML"""
        if not self.notes:
            return
            
        # Quantize all notes
        for note in self.notes:
            note['start_time'] = self._quantize_time(note['start_time'])
            note['duration'] = max(self._quantize_time(note['duration']), 
                                 self.ticks_per_quarter // 4)
    
        # Sort notes by start time
        self.notes.sort(key=lambda x: x['start_time'])
        
        # Create timeline of all events (note starts and ends)
        events = []
        for note in self.notes:
            events.append({
                'time': note['start_time'],
                'type': 'start',
                'note': note
            })
            events.append({
                'time': note['start_time'] + note['duration'],
                'type': 'end',
                'note': note
            })
        
        # Sort events by time
        events.sort(key=lambda x: (x['time'], x['type'] == 'start'))
        
        # Process events and create musical moments
        musical_moments = []
        active_notes = []
        current_time = 0
        
        for event in events:
            event_time = event['time']
            
            # If time has advanced and we have active notes, create a musical moment
            if event_time > current_time and active_notes:
                duration = event_time - current_time
                musical_moments.append({
                    'time': current_time,
                    'duration': duration,
                    'notes': active_notes.copy()
                })
            
            # Update active notes
            if event['type'] == 'start':
                active_notes.append(event['note'])
            else:  # end
                if event['note'] in active_notes:
                    active_notes.remove(event['note'])
            
            current_time = event_time
        
        # Create XML structure
        root = ET.Element('score-partwise', version="3.1")
        
        # Part list
        part_list = ET.SubElement(root, 'part-list')
        score_part = ET.SubElement(part_list, 'score-part', id="P1")
        part_name = ET.SubElement(score_part, 'part-name')
        part_name.text = "Piano"
        
        # Part
        part = ET.SubElement(root, 'part', id="P1")
        
        # Generate measures
        measure_length = self.ticks_per_quarter * 4  # 4/4 time
        current_time = 0
        measure_num = 1
        moment_index = 0
        
        while moment_index < len(musical_moments):
            measure = ET.SubElement(part, 'measure', number=str(measure_num))
            measure_end = current_time + measure_length
            
            # Add attributes to first measure
            if measure_num == 1:
                self._add_measure_attributes(measure)
            
            # Add musical moments in this measure
            while (moment_index < len(musical_moments) and 
                   musical_moments[moment_index]['time'] < measure_end):
                
                moment = musical_moments[moment_index]
                moment_time = moment['time']
                
                # Add rest if needed
                if moment_time > current_time:
                    rest_duration = moment_time - current_time
                    self._add_rest(measure, rest_duration)
                    current_time = moment_time
                
                # Calculate actual duration (clip to measure boundary)
                actual_duration = min(moment['duration'], measure_end - moment_time)
                
                # Add chord/note
                self._add_chord_with_duration(measure, moment['notes'], actual_duration)
                
                current_time = moment_time + actual_duration
                moment_index += 1
            
            # Fill rest of measure with rest if needed
            if current_time < measure_end:
                rest_duration = measure_end - current_time
                self._add_rest(measure, rest_duration)
            
            current_time = measure_end
            measure_num += 1
        
        # Write XML file
        self._write_xml(root, output_filepath)
    
    def _add_measure_attributes(self, measure):
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
        
        # Treble clef
        clef = ET.SubElement(attributes, 'clef')
        sign = ET.SubElement(clef, 'sign')
        sign.text = "G"
        line = ET.SubElement(clef, 'line')
        line.text = "2"
    
    def _add_rest(self, measure, duration):
        """Add rest to measure"""
        note = ET.SubElement(measure, 'note')
        rest = ET.SubElement(note, 'rest')
        
        duration_elem = ET.SubElement(note, 'duration')
        duration_elem.text = str(duration)
        
        note_type = ET.SubElement(note, 'type')
        note_type.text = self._get_note_type(duration)
    
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
    
    def _add_chord_with_duration(self, measure, chord_notes, duration):
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

# Example usage
if __name__ == "__main__":
    convert_midi_to_musicxml("testing/09eded96-ed54-4aab-81f2-6fdb97d32afa.mid", 
                           "testing/09eded96-ed54-4aab-81f2-6fdb97d32afa.musicxml")
