from pydantic import BaseModel
from typing import Optional

class UserJobResponse(BaseModel):
    job_id: str
    status: str
    created_at: str
    result_key: Optional[str] = None  # Make this field optional
    file_name: Optional[str] = None 
    file_size: Optional[int] = None
    file_duration: Optional[int] = None
    
    class Config:
        from_attributes = True