from pydantic import BaseModel
from typing import Optional

class cancelSubscriptionRequest(BaseModel):
    cancelAtPeriodEnd: bool = True  # Default: cancel at end of billing period

class cancelSubscriptionResponse(BaseModel):
    success: bool
    message: str
    subscriptionId: str
    canceledAt: Optional[str] = None
    cancelAtPeriodEnd: bool

class getSubscriptionResponse(BaseModel):
    planName: Optional[str] = None
    price: Optional[str]
    status: Optional[str]
    nextBillingDate: Optional[str]

class getSubscriptionRequest(BaseModel):
    pass