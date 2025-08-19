from pydantic import BaseModel

class UpdateJobRequest(BaseModel):
    job_id: str
    file_name: str

class UpdateJobResponse(BaseModel):
    success: bool
    message: str
