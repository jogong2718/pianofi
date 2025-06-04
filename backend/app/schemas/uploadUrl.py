from pydantic import BaseModel

class CreateUrlPayload(BaseModel):
    user_id: str

class UploadUrlResponse(BaseModel):
    uploadUrl: str
    jobId: str
    fileKey: str