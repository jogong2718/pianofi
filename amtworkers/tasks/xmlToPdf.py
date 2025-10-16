import subprocess
import logging
from pathlib import Path

def convert_musicxml_to_pdf(xml_path, pdf_path, job_id=None, title=None):
    """
    Converts a MusicXML file to a PDF using LilyPond CLI.
    """
    try:
        xml_path = Path(xml_path)
        pdf_path = Path(pdf_path)
        tmp_dir = pdf_path.parent

        logging.info(f"[Job {job_id}] Converting {xml_path.name} → PDF via LilyPond")

        # LilyPond automatically outputs a .pdf next to the .ly file
        cmd = [
            "lilypond",
            "--pdf",
            f"--output={tmp_dir}",
            str(xml_path)
        ]

        subprocess.run(cmd, check=True)

        # LilyPond will create filename.pdf with same basename as input
        generated_pdf = tmp_dir / f"{xml_path.stem}.pdf"
        if generated_pdf.exists():
            generated_pdf.rename(pdf_path)
            logging.info(f"[Job {job_id}] PDF generated at {pdf_path}")
        else:
            logging.error(f"[Job {job_id}] Expected PDF not found after LilyPond run")

    except subprocess.CalledProcessError as e:
        logging.error(f"[Job {job_id}] LilyPond conversion failed: {e}")
    except Exception as e:
        logging.error(f"[Job {job_id}] Unexpected error in PDF conversion: {e}")
