from pydantic import BaseModel, Field
from typing import Optional

class SheetMusicRequest(BaseModel):
    job_id: str
    format: str = "pdf"  # pdf, png, svg, musicxml

class SheetMusicResponse(BaseModel):
    sheet_music_url: str
    filename: str