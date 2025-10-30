import os
import subprocess
import sys
import uuid
import logging
from pathlib import Path

def convert_musicxml_to_pdf(input_path, output_path=None, remove_tagline=True):
    """
    Convert a MusicXML file to PDF using LilyPond.
    
    Args:
        input_path (str): Path to input .xml or .musicxml file.
        output_path (str): Optional path for output PDF (default: same dir as input).
        remove_tagline (bool): Whether to remove LilyPond's footer watermark.

    Returns:
        str: Path to generated PDF file.

    Raises:
        Exception: If conversion fails or dependencies are missing.
    """
    try:
        # Ensure required tools exist
        for cmd in ["musicxml2ly", "lilypond"]:
            if subprocess.call(["which", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
                raise FileNotFoundError(f"Required tool '{cmd}' not found in PATH.")
        
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Prepare working directory
        work_dir = Path(os.getcwd()) / "uploads"
        work_dir.mkdir(parents=True, exist_ok=True)

        # Temporary IDs for intermediate files
        job_id = str(uuid.uuid4())[:8]
        ly_path = work_dir / f"{job_id}.ly"
        pdf_path = work_dir / f"{job_id}.pdf"

        # Step 1: Convert MusicXML → LilyPond (.ly)
        subprocess.run(["musicxml2ly", str(input_path), "-o", str(ly_path)], check=True)

        # Step 2: Remove LilyPond watermark (if requested)
        if remove_tagline:
            with open(ly_path, "a", encoding="utf-8") as f:
                f.write("\n\\paper { tagline = ##f }\n")

        # Step 3: Generate PDF
        subprocess.run(["lilypond", "-o", str(work_dir / job_id), str(ly_path)], check=True)

        # Step 4: Rename final PDF
        final_path = Path(output_path) if output_path else (work_dir / "test.pdf")
        if final_path.exists():
            final_path.unlink()
        pdf_path.rename(final_path)

        logging.info(f"✅ Successfully converted {input_path.name} → {final_path.name}")
        return str(final_path)

    except subprocess.CalledProcessError as e:
        raise Exception(f"Conversion failed: {e}")
    except Exception as e:
        raise Exception(f"Error: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python xmlToPdf.py <input_musicxml> [output_pdf]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) >= 3 else None

    try:
        result = convert_musicxml_to_pdf(input_file, output_file)
        print(f"PDF created: {result}")
    except Exception as e:
        print(f"❌ {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
