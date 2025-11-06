from pydantic import BaseModel
from typing import Dict, Any

class CreateCheckoutSessionRequest(BaseModel):
    priceId: str

class CreateCheckoutSessionResponse(BaseModel):
    sessionId: str
    checkoutUrl: str