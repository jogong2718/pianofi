from pydantic import BaseModel

class CreateUrlPayload(BaseModel):
    file_name: str
    file_size: int
    content_type: str

class UploadUrlResponse(BaseModel):
    uploadUrl: str
    jobId: str
    fileKey: str