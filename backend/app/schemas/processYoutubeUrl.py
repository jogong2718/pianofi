from pydantic import BaseModel, HttpUrl

class ProcessYoutubeUrlPayload(BaseModel):
    youtube_url: str
    model: str
    level: int

class ProcessYoutubeUrlResponse(BaseModel):
    jobId: str
    fileKey: str
    success: bool
