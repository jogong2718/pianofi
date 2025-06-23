from pydantic import BaseModel
from typing import Optional

class UserJobResponse(BaseModel):
    job_id: str
    status: str
    created_at: str
    result_key: Optional[str] = None  # Make this field optional
    
    class Config:
        from_attributes = True