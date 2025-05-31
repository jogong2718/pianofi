# app/schemas/upload.py
from pydantic import BaseModel

class UploadUrlResponse(BaseModel):
    uploadUrl: str
    jobId: str
    fileKey: str