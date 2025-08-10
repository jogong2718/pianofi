from pydantic import BaseModel

class CreateJobPayload(BaseModel):
    jobId: str
    fileKey: str
    model: str
    level: int

class CreateJobResponse(BaseModel):
    success: bool