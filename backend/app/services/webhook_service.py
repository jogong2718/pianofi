"""
Webhook Service - Handles incoming webhook events.

Functions for webhook signature verification, event routing, and idempotency.
Serves routers: webhooks
"""

from typing import Dict, Any
import logging

import stripe
from app.config_loader import Config
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.repositories.webhook_event_repository import (
    upsert_customer,
    upsert_subscription_from_stripe,
    user_id_from_customer,
    commit,
    rollback,
    get_active_subscriptions_for_user,
    mark_subscription_canceled,
)

logger = logging.getLogger(__name__)

def handle_stripe_webhook(payload: bytes, sig: str, db: Session) -> Dict[str, Any]:
    """
    Verify signature, route events, perform DB writes using repository functions.
    Raises stripe.error.SignatureVerificationError for invalid signature.
    Raises other exceptions for processing errors (caller should map to HTTP response).
    """
    stripe.api_key = Config.STRIPE_KEYS["secret_key"]
    WEBHOOK_SECRET = Config.STRIPE_KEYS["webhook_secret"]

    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        # Let caller translate signature error to HTTP 400
        raise

    etype = event["type"]
    obj = event["data"]["object"]
    logger.info(f"Stripe webhook {etype} id={event['id']}")

    try:
        # 1) Checkout completed: link user<->customer<->subscription and write subscription (Stripe times)
        if etype == "checkout.session.completed":
            logging.info(f"Checkout session completed: {obj.get('id')}")
            session = obj
            sub_id = session.get("subscription")
            cust_id = session.get("customer")

            # Prefer user_id from session metadata (we set it when creating Checkout Session)
            user_id = (session.get("metadata") or {}).get("user_id")

            # If missing, fetch subscription and read its metadata
            if (not user_id) and sub_id:
                sub = stripe.Subscription.retrieve(sub_id)
                user_id = (sub.get("metadata") or {}).get("user_id")

            if not (user_id and cust_id and sub_id):
                raise RuntimeError("Missing user_id/customer/subscription in checkout.session.completed")

            # Upsert customer row and subscription row (with Stripe-created timestamps)
            upsert_customer(db, user_id=user_id, stripe_customer_id=cust_id)
            sub = stripe.Subscription.retrieve(sub_id)
            upsert_subscription_from_stripe(db, sub=sub, user_id=user_id)

            # If this subscription is active, cancel previous subscriptions for this user
            if sub.get("status") == "active":
                other_subs = get_active_subscriptions_for_user(db, user_id, exclude_id=sub["id"])
                for other_id in other_subs:
                    try:
                        canceled = stripe.Subscription.delete(other_id)
                        # stripe returns canceled_at as epoch seconds (or None)
                        canceled_at_ts = canceled.get("canceled_at")
                        canceled_at = datetime.fromtimestamp(canceled_at_ts, tz=timezone.utc) if canceled_at_ts else None
                        mark_subscription_canceled(db, other_id, canceled_at)
                    except Exception:
                        logger.exception(f"Failed to cancel previous subscription {other_id}; continuing")

            commit(db)
            return {"ok": True}

        # 2) Subscription lifecycle: create/update/delete (delete = status='canceled' provided by Stripe)
        if etype in ("customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"):
            logging.info(f"Processing subscription {etype}: {obj.get('id')}")
            sub = obj
            cust_id = sub.get("customer")

            # Find our user; if missing (rare), fall back to subscription metadata
            user_id = user_id_from_customer(db, cust_id) if cust_id else None
            if not user_id:
                user_id = (sub.get("metadata") or {}).get("user_id")
                if not user_id:
                    logger.warning(f"No user_id for subscription {sub['id']}; skipping upsert")
                    return {"ok": True}

            upsert_customer(db, user_id=user_id, stripe_customer_id=cust_id)
            upsert_subscription_from_stripe(db, sub=sub, user_id=user_id)

            # If this subscription is active, cancel previous subscriptions for this user
            if sub.get("status") == "active":
                other_subs = get_active_subscriptions_for_user(db, user_id, exclude_id=sub["id"])
                for other_id in other_subs:
                    try:
                        canceled = stripe.Subscription.delete(other_id)
                        canceled_at_ts = canceled.get("canceled_at")
                        canceled_at = datetime.fromtimestamp(canceled_at_ts, tz=timezone.utc) if canceled_at_ts else None
                        mark_subscription_canceled(db, other_id, canceled_at)
                    except Exception:
                        logger.exception(f"Failed to cancel previous subscription {other_id}; continuing")

            commit(db)
            return {"ok": True}

        # 3) (Optional) Acknowledge invoice events quickly (no DB writes for MVP)
        if etype in ("invoice.paid", "invoice.payment_succeeded"):
            logger.info(f"Invoice paid: {obj.get('id')} sub={obj.get('subscription')}")
            return {"ok": True}

        # Ignore everything else for MVP
        return {"ok": True}

    except Exception:
        rollback(db)
        logger.exception("Stripe webhook handling error")
        raise
