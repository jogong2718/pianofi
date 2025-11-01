from pydantic import BaseModel
from typing import Dict, Any

class CreateCheckoutSessionRequest(BaseModel):
    priceId: str
    successUrl: str
    cancelUrl: str
    metadata: Dict[str, Any] = None

class CreateCheckoutSessionResponse(BaseModel):
    sessionId: str
    checkoutUrl: str