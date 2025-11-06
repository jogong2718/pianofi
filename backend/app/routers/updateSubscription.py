from fastapi import APIRouter, HTTPException, Depends, Request
from app.schemas.updateSubscription import cancelSubscriptionRequest, cancelSubscriptionResponse, getSubscriptionResponse, getSubscriptionRequest
from app.schemas.user import User
from app.auth import get_current_user
from app.config_loader import Config
from app.services.payment_service import cancel_subscription, get_subscription
from app.database import get_db
from sqlalchemy.orm import Session
import stripe
import logging

router = APIRouter()

# Initialize Stripe with your secret key
stripe.api_key = Config.STRIPE_KEYS['secret_key']

@router.post("/cancelSubscription", response_model=cancelSubscriptionResponse)
async def cancel_subscription_endpoint(
    request: Request,
    payload: cancelSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel the user's active subscription.
    
    - **cancelAtPeriodEnd**: If true, cancel at end of billing period. If false, cancel immediately.
    
    Stripe webhook will handle updating the database with the cancellation details.
    """
    try:
        result = cancel_subscription(
            user_id=current_user.id,
            cancel_at_period_end=payload.cancelAtPeriodEnd,
            stripe_client=stripe,
            db=db
        )
        
        logging.info(
            f"Subscription cancellation requested for user {current_user.id}, "
            f"subscription_id={result['subscription_id']}, "
            f"at_period_end={payload.cancelAtPeriodEnd}"
        )
    # success: bool
    # message: str
    # subscriptionId: str
    # canceledAt: Optional[str] = None
    # cancelAtPeriodEnd: bool
        return cancelSubscriptionResponse(
            success=result["success"],
            message=result["message"],
            subscriptionId=result["subscription_id"],
            canceledAt=result["canceled_at"],
            cancelAtPeriodEnd=payload.cancelAtPeriodEnd
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/getSubscription", response_model=getSubscriptionResponse)
async def get_subscription_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the user's active subscription details.
    """
    try:
        logging.info(f"Fetching subscription for user {current_user.id}")
        subscription = get_subscription(
            user_id=current_user.id,
            stripe_client=stripe,
            db=db
        )

        logging.info(f"Subscription fetched for user {current_user.id}: {subscription}")

        return getSubscriptionResponse(
            planName=subscription["planName"], 
            price=str(subscription["price"]),
            status=subscription["status"], 
            nextBillingDate=subscription["nextBillingDate"]
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/test")
async def test_endpoint():
    return {"message": "Router is working"}