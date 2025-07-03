from pydantic import BaseModel

class CreateCheckoutSessionRequest(BaseModel):
    priceId: str

class CreateCheckoutSessionResponse(BaseModel):
    sessionId: str