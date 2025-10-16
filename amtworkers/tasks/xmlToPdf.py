# amtworkers/tasks/xmlToPdf.py
import subprocess
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def convert_musicxml_to_pdf(xml_path: str, pdf_path: str, timeout: int = 60):
    """
    Convert a MusicXML file to PDF using the verovio CLI.
    Expects `verovio` binary to be available on PATH.
    """
    xml = Path(xml_path)
    pdf = Path(pdf_path)

    if not xml.exists():
        raise FileNotFoundError(f"Input XML not found: {xml}")

    cmd = ["verovio", str(xml), "-o", str(pdf)]
    logger.info(f"Running verovio: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        logger.info(f"verovio stdout: {result.stdout}")
        logger.info(f"verovio stderr: {result.stderr}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Verovio conversion failed: {e.stderr}")
        raise
    except Exception:
        logger.exception("Verovio conversion exception")
        raise

    if not pdf.exists():
        raise RuntimeError(f"Verovio did not produce PDF at {pdf}")

    return str(pdf)
