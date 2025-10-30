from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class getDownloadResponse(BaseModel):
    job_id: str
    status: str
    midi_download_url: Optional[str] = None
    xml_download_url: Optional[str] = None
    pdf_download_url: Optional[str] = None