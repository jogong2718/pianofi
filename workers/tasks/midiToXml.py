import logging
from pathlib import Path
from music21 import converter

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
        
        # Parse MIDI file
        score = converter.parse(midi_file_path)
        
        # Apply quantization to clean up timing
        score.quantize(
            quarterLengthDivisors=[4, 3], 
            processOffsets=True, 
            processDurations=True
        )
        
        # Write to MusicXML
        score.write("musicxml", output_path)
        
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