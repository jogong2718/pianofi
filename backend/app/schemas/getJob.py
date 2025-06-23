from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class GetJobResponse(BaseModel):
    job_id: str
    status: str
    download_url: Optional[str] = None