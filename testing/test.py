import sys
from pathlib import Path
from music21 import converter, stream, clef, meter, key
import tempfile
import copy

def test_midi_to_xml(midi_file_path):
    """Test MIDI to XML conversion with treble/bass clef separation"""
    try:
        print(f"Testing conversion of: {midi_file_path}")
        
        # Parse MIDI
        score = converter.parse(midi_file_path)
        print(f"✓ Successfully parsed MIDI file")
        
        # Apply quantization (same as worker)
        score.quantize(
            quarterLengthDivisors=[4, 3],  # More strict - only common note values
            processOffsets=True, 
            processDurations=True,
            inPlace=True,
            recurse=True
        )
        print(f"✓ Applied quantization")
        
        # Create piano score with treble and bass clefs
        piano_score = create_piano_score(score)
        print(f"✓ Separated into treble and bass clefs")
        
        # Save to current directory instead of temp
        midi_name = Path(midi_file_path).stem  # Get filename without extension
        xml_path = f"{midi_name}.xml"
        
        piano_score.write("musicxml", xml_path)
        print(f"✓ Converted to XML: {xml_path}")
        
        # Check file size
        xml_size = Path(xml_path).stat().st_size
        print(f"✓ XML file size: {xml_size} bytes")
        
        return xml_path
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def create_piano_score(original_score):
    """Create a piano score with treble and bass clefs"""
    from music21 import note, chord, layout, stream, duration, pitch
    
    # Create new score
    piano_score = stream.Score()
    
    # Add metadata if present
    if original_score.metadata:
        piano_score.metadata = original_score.metadata
    
    # Create treble and bass staves as separate parts
    treble_part = stream.Part()
    treble_part.id = 'Piano-Treble'
    treble_part.partName = 'Piano'
    treble_part.insert(0, clef.TrebleClef())
    
    bass_part = stream.Part()
    bass_part.id = 'Piano-Bass' 
    bass_part.partName = 'Piano'
    bass_part.insert(0, clef.BassClef())
    
    # Add time signature and key signature from original if present
    time_sig = None
    key_sig = None
    for element in original_score.flatten():
        if isinstance(element, meter.TimeSignature) and time_sig is None:
            time_sig = copy.deepcopy(element)
            treble_part.insert(0, time_sig)
            bass_part.insert(0, copy.deepcopy(element))
        elif isinstance(element, key.KeySignature) and key_sig is None:
            key_sig = copy.deepcopy(element)
            treble_part.insert(0, key_sig)
            bass_part.insert(0, copy.deepcopy(element))
    
    # If no time signature found, add default 4/4
    if time_sig is None:
        default_ts = meter.TimeSignature('4/4')
        treble_part.insert(0, default_ts)
        bass_part.insert(0, meter.TimeSignature('4/4'))
    
    # Define staff ranges (MIDI note numbers)
    TREBLE_MIN = 60   # C4 (Middle C)
    TREBLE_MAX = 84   # C6 (High C)
    BASS_MIN = 36     # C2 (Low C)
    BASS_MAX = 72     # C5 (Tenor C)
    
    # Middle C (C4) is around MIDI note 60, use this as split point
    SPLIT_PITCH = 60  # Middle C
    
    # Collect notes for each staff with timing
    treble_notes = []
    bass_notes = []
    
    # Only process notes and chords, skip rests entirely
    for element in original_score.flatten().notes:
        if element.isNote:
            note_copy = copy.deepcopy(element)
            midi_num = element.pitch.midi
            if midi_num >= SPLIT_PITCH:
                treble_notes.append((element.offset, note_copy))
            else:
                bass_notes.append((element.offset, note_copy))
                
        elif element.isChord:
            # Split chord notes based on pitch
            treble_chord_notes = []
            bass_chord_notes = []
            
            for pitch in element.pitches:
                if pitch.midi >= SPLIT_PITCH:
                    treble_chord_notes.append(pitch)
                else:
                    bass_chord_notes.append(pitch)
            
            # Create new chords for each staff
            if treble_chord_notes:
                treble_chord = chord.Chord(treble_chord_notes, 
                                         quarterLength=element.quarterLength)
                treble_notes.append((element.offset, treble_chord))
            
            if bass_chord_notes:
                bass_chord = chord.Chord(bass_chord_notes, 
                                       quarterLength=element.quarterLength)
                bass_notes.append((element.offset, bass_chord))
    
    # Sort notes by offset
    treble_notes.sort(key=lambda x: x[0])
    bass_notes.sort(key=lambda x: x[0])
    
    # Add notes with proper timing and constrained rests
    def add_notes_with_timing(part, notes_list, staff_min, staff_max):
        if not notes_list:
            return
            
        for offset, note_obj in notes_list:
            # Add the note at its proper offset, music21 will handle timing
            part.insert(offset, note_obj)
    
    add_notes_with_timing(treble_part, treble_notes, TREBLE_MIN, TREBLE_MAX)
    add_notes_with_timing(bass_part, bass_notes, BASS_MIN, BASS_MAX)
    
    # Add both parts to score
    piano_score.insert(0, treble_part)
    piano_score.insert(0, bass_part)
    
    # Fill gaps with rests without altering timing
    piano_score.makeRests(inPlace=True)
    
    return piano_score


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_midi_xml.py <midi_file_path>")
        sys.exit(1)
    
    midi_path = sys.argv[1]
    xml_path = test_midi_to_xml(midi_path)
    
    if xml_path:
        print(f"\nSuccess! XML saved to: {xml_path}")
    else:
        print("\nConversion failed!")