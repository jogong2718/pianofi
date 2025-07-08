from pydantic import BaseModel

class UpdateProfileRequest(BaseModel):
    first_name: str
    last_name: str

class UpdateProfileResponse(BaseModel):
    success: bool
    message: str
    user: dict