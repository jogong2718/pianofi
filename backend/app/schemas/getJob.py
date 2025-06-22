from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class GetJobResponse(BaseModel):
    jobId: str
    status: str
    downloadUrl: Optional[str] = None