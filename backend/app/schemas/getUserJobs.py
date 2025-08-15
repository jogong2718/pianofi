from pydantic import BaseModel
from typing import Optional

class UserJobResponse(BaseModel):
    job_id: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    status: str
    created_at: Optional[str] = None
    queued_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    model: Optional[str] = None
    level: Optional[int] = None
    
    class Config:
        from_attributes = True