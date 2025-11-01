from fastapi import APIRouter, HTTPException, Depends, Request
from app.schemas.createCheckoutSession import CreateCheckoutSessionRequest, CreateCheckoutSessionResponse
from app.schemas.user import User
from app.auth import get_current_user
from app.config_loader import Config
from app.services.payment_service import create_stripe_checkout_session
import stripe
import logging

router = APIRouter()

# Initialize Stripe with your secret key
stripe.api_key = Config.STRIPE_KEYS['secret_key']

@router.post("/createCheckoutSession", response_model=CreateCheckoutSessionResponse)
async def create_checkout_session(
    request: Request,
    payload: CreateCheckoutSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a Stripe checkout session for subscription payment
    """
    try:
        session_data = create_stripe_checkout_session(
            user_id=current_user.id,
            price_id=payload.priceId,
            success_url=payload.successUrl,
            cancel_url=payload.cancelUrl,
            metadata=payload.metadata,
            stripe_client=stripe,
            payment_repository=request.app.state.payment_repository,
            user_repository=request.app.state.user_repository
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