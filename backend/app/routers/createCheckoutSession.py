from fastapi import APIRouter, HTTPException, Depends, Request
from app.schemas.createCheckoutSession import CreateCheckoutSessionRequest, CreateCheckoutSessionResponse
from app.schemas.user import User
from app.auth import get_current_user
from app.config_loader import Config
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
        # Get the origin from request header
        origin = request.headers.get("origin")
        
        # If no origin header, use the first allowed CORS origin as fallback
        if not origin:
            cors_origins = Config.CORS_ORIGINS
            origin = cors_origins[0] if cors_origins else "http://localhost:3000"

        # Find or create Stripe customer
        stripe_customer = None
        
        # First, try to find existing customer by email
        customers = stripe.Customer.list(email=current_user.email, limit=1)
        if customers.data:
            stripe_customer = customers.data[0]
            logging.info(f"Found existing Stripe customer: {stripe_customer.id}")
        else:
            # Create new customer if none exists
            stripe_customer = stripe.Customer.create(
                email=current_user.email,
                metadata={
                    'user_id': str(current_user.id)
                }
            )
            logging.info(f"Created new Stripe customer: {stripe_customer.id}")

        try:
            existing_subscription = stripe.Subscription.list(
                customer=stripe_customer.id,
                status='active',
                limit=100
            )

            for subscription in existing_subscription.data:
                logging.info(f"Canceling existing subscription: {subscription.id}")
                stripe.Subscription.delete(subscription.id)

        except stripe.error.StripeError as e:
            logging.error(f"Error checking existing subscriptions: {str(e)}")
                
        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': payload.priceId,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{origin}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{origin}/dashboard",
            customer=stripe_customer.id,
            subscription_data={
                'metadata': {
                    'user_id': str(current_user.id),
                }
            },
            metadata={
                'user_id': str(current_user.id),
            }
        )
        
        return CreateCheckoutSessionResponse(sessionId=session.id)
        
    except stripe.error.StripeError as e:
        logging.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        logging.error(f"Checkout session creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")