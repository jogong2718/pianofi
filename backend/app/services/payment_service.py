"""
Payment Service - Handles payment and subscription logic.

Functions for Stripe checkout, webhooks, and subscription management.
Serves routers: createCheckoutSession, webhook payment events
"""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import logging
import stripe
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def create_checkout_session(
    user_id: UUID,
    user_email: str,
    price_id: str,
    stripe_client,
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
    db=None
) -> Dict[str, Any]:
    logger.info(f"Creating checkout session for user {user_id}, price {price_id}")

    if not price_id:
        raise ValueError("price_id is required")

    # Provide reasonable defaults if caller didn't
    success_url = success_url or "https://www.pianofi.ca/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = cancel_url or "https://www.pianofi.ca/dashboard"

    try:
        # Get or create Stripe customer id via repository helper
        customer_id = _get_or_create_customer(user_id, user_email, stripe_client, db)

        # Create Stripe checkout session
        session = stripe_client.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            customer=customer_id,
            allow_promotion_codes=True,
            subscription_data={
                'metadata': {'user_id': str(user_id)}
            },
            metadata={'user_id': str(user_id)}
        )

        checkout_url = getattr(session, "url", None) or session.get("url") if isinstance(session, dict) else None

        return {"session_id": session.id, "checkout_url": checkout_url or ""}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise RuntimeError(f"Stripe error: {e}")
    except Exception as e:
        logger.error(f"Checkout session creation failed: {e}")
        raise RuntimeError("Failed to create checkout session")



def handle_payment_success(
    session_id: str,
    stripe_data: Dict[str, Any],
    payment_repository,
    user_repository
) -> None:
    """
    Handle successful payment webhook event.
    
    Business logic:
    1. Retrieve checkout session
    2. Update user subscription status
    3. Grant access/quota
    4. Send confirmation email
    
    Args:
        session_id: Stripe checkout session ID
        stripe_data: Full Stripe event data
        payment_repository: Repository for payment data
        user_repository: Repository for user data
    """
    logger.info(f"Processing payment success for session {session_id}")
    
    # TODO: Implement
    # 1. Get session details
    # 2. Update user: user_repository.update_subscription_status(user_id, "active")
    # 3. Record payment: payment_repository.save_payment(...)
    # 4. Send notification
    
    raise NotImplementedError()


def handle_subscription_updated(
    subscription_id: str,
    stripe_data: Dict[str, Any],
    payment_repository,
    user_repository
) -> None:
    """
    Handle subscription update webhook event.
    
    Args:
        subscription_id: Stripe subscription ID
        stripe_data: Full Stripe event data
        payment_repository: Repository for payment data
        user_repository: Repository for user data
    """
    logger.info(f"Processing subscription update for {subscription_id}")
    
    # TODO: Implement
    # 1. Get subscription details
    # 2. Update DB: payment_repository.update_subscription(...)
    # 3. Adjust user quota/access based on new plan
    
    raise NotImplementedError()


def handle_subscription_cancelled(
    subscription_id: str,
    stripe_data: Dict[str, Any],
    payment_repository,
    user_repository
) -> None:
    """
    Handle subscription cancellation webhook event.
    
    Args:
        subscription_id: Stripe subscription ID
        stripe_data: Full Stripe event data
        payment_repository: Repository for payment data
        user_repository: Repository for user data
    """
    logger.info(f"Processing subscription cancellation for {subscription_id}")
    
    # TODO: Implement
    # 1. Update subscription status in DB
    # 2. Revoke premium access (but keep data)
    # 3. Send cancellation confirmation
    
    raise NotImplementedError()


def get_subscription_status(user_id: UUID, payment_repository) -> Dict[str, Any]:
    """
    Get current subscription status for a user.
    
    Args:
        user_id: UUID of the user
        payment_repository: Repository for payment data
    
    Returns:
        Dict containing subscription details (status, plan, next_billing_date, etc.)
    """
    logger.info(f"Getting subscription status for user {user_id}")
    
    # TODO: Implement
    # subscription = payment_repository.get_active_subscription(user_id)
    # return subscription.to_dict() if subscription else {"status": "none"}
    
    raise NotImplementedError()


def _get_or_create_customer(
    user_id: UUID,
    user_email: str,
    stripe_client,
    db
) -> str:
    """
    Get existing Stripe customer ID or create a new customer.
    
    Args:
        user_id: UUID of the user
        user_email: Email of the user
        stripe_client: Client for Stripe operations
        db: Database session
    
    Returns:
        Stripe customer ID
    """

    from app.repositories import payment_repository
    from app.repositories import webhook_event_repository

    try:
        user = payment_repository.find_user_stripe_customer_id(db=db, user_id=user_id)

        if user:
            logging.info(f"Found existing Stripe customer ID for user {user_id}")
            return user["stripe_customer_id"]
        else:
            logging.info(f"Creating new Stripe customer for user {user_id}")
            customer = stripe_client.Customer.create(email=user_email, metadata={"user_id": str(user_id)})
            webhook_event_repository.upsert_customer(db, user_id=str(user_id), stripe_customer_id=customer.id)
            db.commit()

            logger.info(f"Created Stripe customer {customer.id} for user {user_id}")
            return customer.id
    except Exception as e:
        logger.error(f"Failed to get or create Stripe customer for user {user_id}: {e}")
        raise RuntimeError("Failed to get or create Stripe customer")


def cancel_subscription(
    user_id: UUID,
    cancel_at_period_end: bool,
    stripe_client,
    db
) -> Dict[str, Any]:
    """
    Cancel a user's active subscription via Stripe.
    Stripe webhook will handle updating the database.
    
    Args:
        user_id: UUID of the user
        cancel_at_period_end: If True, cancel at end of billing period. If False, cancel immediately.
        stripe_client: Stripe client instance
        payment_repository: Repository for payment data
        db: Database session
    
    Returns:
        Dict with cancellation details
    """
    from app.repositories import payment_repository

    logger.info(f"Cancelling subscription for user {user_id}, at_period_end={cancel_at_period_end}")
    
    # Get user's active subscription
    subscription_id = payment_repository.get_active_subscription_id(db, str(user_id))
    
    if not subscription_id:
        raise ValueError("No active subscription found for user")
    
    try:
        # Cancel via Stripe API - webhook will update DB
        if cancel_at_period_end:
            # Cancel at end of billing period
            subscription = stripe_client.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            canceled_at = None
            message = "Subscription will be cancelled at the end of the billing period"
        else:
            # Cancel immediately
            subscription = stripe_client.Subscription.delete(subscription_id)
            canceled_at = subscription.get("canceled_at")
            if canceled_at:
                from datetime import datetime, timezone
                canceled_at = datetime.fromtimestamp(canceled_at, tz=timezone.utc)
            message = "Subscription cancelled immediately"
        
        return {
            "success": True,
            "message": message,
            "subscription_id": subscription_id,
            "canceled_at": canceled_at.isoformat() if canceled_at else None,
            "cancel_at_period_end": cancel_at_period_end
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error cancelling subscription: {e}")
        raise RuntimeError(f"Failed to cancel subscription: {str(e)}")
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise RuntimeError(f"Failed to cancel subscription: {str(e)}")

def get_subscription(
    user_id: UUID,
    stripe_client,
    db
) -> Dict[str, Any]:
    """
    Get the user's active subscription details.
    
    Args:
        user_id: UUID of the user
        stripe_client: Stripe client instance
        payment_repository: Repository for payment data
        db: Database session
    
    Returns:
        Dict containing subscription details
    """
    from app.repositories import payment_repository

    logger.info(f"Getting subscription for user {user_id}")
    
    # Get user's active subscription ID
    subscription_id = payment_repository.get_active_subscription_id(db, str(user_id))
    
    if not subscription_id:
        return {"planName": None, "price": None, "status": None, "nextBillingDate": None}
    
    try:
        # Retrieve subscription details from Stripe
        subscription = stripe_client.Subscription.retrieve(subscription_id)

        logging.info(f"Retrieved subscription from Stripe at id {subscription_id}")

        items = subscription.get("items", {}).get("data", [])

        if not items:
            return {"planName": None, "price": None, "status": None, "nextBillingDate": None}

        price = items[0].get("price") or {}

        cpe = items[0].get("current_period_end")  # int seconds or None
        next_billing = datetime.fromtimestamp(cpe, tz=timezone.utc).isoformat() if cpe else None

        logging.info(f"Subscription details - Plan: {price.get('nickname')}, Price: {price.get('unit_amount')}, Status: {subscription.get('status')}, Next Billing: {next_billing}")
        
        return {
            "planName": price.get("nickname") or ("Standard Plan" if price.get("unit_amount") == 499 else "None"),
            "price": (price.get("unit_amount") or 0) / 100,
            "status": subscription.get("status"),
            "nextBillingDate": next_billing,
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error retrieving subscription: {e}")
        raise RuntimeError(f"Failed to retrieve subscription: {str(e)}")
    except Exception as e:
        logger.error(f"Error retrieving subscription: {e}")
        raise RuntimeError(f"Failed to retrieve subscription: {str(e)}")