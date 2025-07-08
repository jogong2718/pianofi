from pydantic import BaseModel, Field
from typing import Optional

class deleteJobResponse(BaseModel):
    message: str
    jobId: str