from pydantic import BaseModel

class CreateJobPayload(BaseModel):
    jobId: str
    fileKey: str
    userId: str

class CreateJobResponse(BaseModel):
    success: bool