from pydantic import BaseModel
from typing import Optional

class CreateCheckoutSessionRequest(BaseModel):
    priceId: str
    uiMode: str = "hosted"

class CreateCheckoutSessionResponse(BaseModel):
    sessionId: str
    checkoutUrl: str
    clientSecret: Optional[str] = None