from pydantic import BaseModel

class CreateJobPayload(BaseModel):
    jobId: str
    fileKey: str

class CreateJobResponse(BaseModel):
    success: bool