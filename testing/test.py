import sys
from pathlib import Path
from music21 import converter, stream, clef, meter, key, chord, note
import tempfile
import copy

def test_midi_to_xml(midi_file_path):
    """Test MIDI to XML conversion with treble/bass clef separation"""
    try:
        print(f"Testing conversion of: {midi_file_path}")
        
        # Parse MIDI
        score = converter.parse(midi_file_path)
        print(f"✓ Successfully parsed MIDI file")
        
        # # Apply quantization (same as worker)
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
        xml_path = f"{midi_name}.musicxml"
        
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
    """
    Split a piano MIDI into two staves (treble/bass),
    preserving exact measure structure and offsets.
    """
    # We’ll assume the MIDI has a single piano Part.
    src_part = original_score.parts[0]

    # Prepare new Score and Parts
    piano_score = stream.Score()
    treble_part = stream.Part()
    bass_part   = stream.Part()

    # Add clefs at the very beginning
    treble_part.insert(0, clef.TrebleClef())
    bass_part.insert(0,   clef.BassClef())

    SPLIT = 60  # Middle C

    # Iterate each measure in source
    for m in src_part.getElementsByClass(stream.Measure):
        # Create two empty measures with the same number & time/key signatures
        m_num = m.measureNumber
        m_ts  = copy.deepcopy(m.timeSignature) if m.timeSignature else None
        m_ks  = copy.deepcopy(m.keySignature)  if m.keySignature  else None

        treb_m = stream.Measure(number=m_num)
        bass_m = stream.Measure(number=m_num)
        if m_ts: 
            treb_m.timeSignature = m_ts
            bass_m.timeSignature = copy.deepcopy(m_ts)
        if m_ks:
            treb_m.keySignature = m_ks
            bass_m.keySignature = copy.deepcopy(m_ks)

        # Copy notes/chords/rests into the “right” measure
        for el in m.notesAndRests:
            # el.offset is *within* the measure already
            if isinstance(el, note.Note):
                target = treb_m if el.pitch.midi >= SPLIT else bass_m
                target.insert(el.offset, copy.deepcopy(el))
            elif isinstance(el, chord.Chord):
                high = [p for p in el.pitches if p.midi >= SPLIT]
                low  = [p for p in el.pitches if p.midi <  SPLIT]
                if high:
                    c2 = chord.Chord(high, quarterLength=el.quarterLength)
                    treb_m.insert(el.offset, c2)
                if low:
                    c3 = chord.Chord(low,  quarterLength=el.quarterLength)
                    bass_m.insert(el.offset, c3)
            else:
                # e.g. a Rest—copy into both staves so measures sum correctly
                treb_m.insert(el.offset, copy.deepcopy(el))
                bass_m.insert(el.offset, copy.deepcopy(el))

        # Append these measures in sequence
        treble_part.append(treb_m)
        bass_part.append(bass_m)

    # Finally, add the two parts to the score
    piano_score.insert(0, treble_part)
    piano_score.insert(0, bass_part)
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