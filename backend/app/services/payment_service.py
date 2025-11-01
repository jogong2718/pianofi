"""
Payment Service - Handles payment and subscription logic.

Functions for Stripe checkout, webhooks, and subscription management.
Serves routers: createCheckoutSession, webhook payment events
"""

from typing import Dict, Any, Optional
from uuid import UUID
import logging
import stripe

logger = logging.getLogger(__name__)


def create_checkout_session(
    user_id: UUID,
    price_id: str,
    success_url: Optional[str],
    cancel_url: Optional[str],
    metadata: Optional[Dict[str, Any]],
    stripe_client,
    payment_repository,
    user_repository
) -> Dict[str, Any]:
    logger.info(f"Creating checkout session for user {user_id}, price {price_id}")

    if not price_id:
        raise ValueError("price_id is required")

    # Provide reasonable defaults if caller didn't
    success_url = success_url or "https://www.pianofi.ca/success?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = cancel_url or "https://www.pianofi.ca/dashboard"

    try:
        # Get or create Stripe customer id via repository helper
        customer_id = _get_or_create_customer(user_id, stripe_client, user_repository)

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
            subscription_data={
                'metadata': metadata or {'user_id': str(user_id)}
            },
            metadata=metadata or {'user_id': str(user_id)}
        )

        # Persist session record in payment repository if available
        try:
            if payment_repository:
                # adapt to your repository API; example method names
                payment_repository.save_checkout_session({
                    "user_id": str(user_id),
                    "stripe_session_id": session.id,
                    "price_id": price_id,
                    "status": getattr(session, "status", "open")
                })
        except Exception as e:
            logger.warning(f"Failed to persist checkout session: {e}")

        checkout_url = getattr(session, "url", None) or session.get("url") if isinstance(session, dict) else None
        # Some stripe lib versions return session.url, others provide a hosted_checkout_url or require building URL with id.
        # Return both id and url if available.
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
    stripe_client,
    user_repository
) -> str:
    """
    Get existing Stripe customer ID or create a new customer.
    
    Args:
        user_id: UUID of the user
        stripe_client: Client for Stripe operations
        user_repository: Repository for user data
    
    Returns:
        Stripe customer ID
    """
    # TODO: Implement
    # user = user_repository.find_by_id(user_id)
    # if user.stripe_customer_id:
    #     return user.stripe_customer_id
    # customer = stripe_client.create_customer(email=user.email, metadata={"user_id": str(user_id)})
    # user_repository.update(user_id, {"stripe_customer_id": customer.id})
    # return customer.id
    
    raise NotImplementedError()
