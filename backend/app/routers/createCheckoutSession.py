from fastapi import APIRouter, HTTPException, Depends, Request
from app.schemas.createCheckoutSession import CreateCheckoutSessionRequest, CreateCheckoutSessionResponse
from app.schemas.user import User
from app.auth import get_current_user
from app.config_loader import Config
from app.services.payment_service import create_checkout_session
from app.database import get_db
import stripe
import logging

router = APIRouter()

# Initialize Stripe with your secret key
stripe.api_key = Config.STRIPE_KEYS['secret_key']

@router.post("/createCheckoutSession", response_model=CreateCheckoutSessionResponse)
async def create_checkout_session_endpoint(
    request: Request,
    payload: CreateCheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Create a Stripe checkout session for subscription payment
    """

    origin = request.headers.get("origin")
    allowed = Config.CORS_ORIGINS
    if origin and allowed:
        # only allow known origins
        origin = origin if origin in allowed else "https://www.pianofi.ca"
    elif not origin:
        origin = "https://www.pianofi.ca"

    success_url = f"{origin}/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin}/dashboard"

    try:

        session_data = create_checkout_session(
            user_id=current_user.id,
            user_email=current_user.email,
            price_id=payload.priceId,
            stripe_client=stripe,
            success_url=success_url,
            cancel_url=cancel_url,
            db=db
        )
        
        logging.info(
            f"Checkout session created for user {current_user.id}, "
            f"price {payload.priceId}"
        )
        
        return CreateCheckoutSessionResponse(
            sessionId=session_data["session_id"],
            checkoutUrl=session_data["checkout_url"]
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))