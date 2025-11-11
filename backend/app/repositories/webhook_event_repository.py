"""
Webhook Event Repository - Data access for webhook_events table.

Used by: WebhookService
Table: webhook_events (for idempotency tracking)
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import json

logger = logging.getLogger(__name__)

def _ts(sec: Optional[int]) -> Optional[datetime]:
    return datetime.fromtimestamp(sec, tz=timezone.utc) if sec else None

def upsert_customer(db: Session, *, user_id: str, stripe_customer_id: str) -> None:
    """
    customers(id uuid PK, stripe_customer_id text NOT NULL)
    """
    db.execute(
        text("""
            INSERT INTO customers (id, stripe_customer_id)
            VALUES (:user_id, :cust)
            ON CONFLICT (id)
            DO UPDATE SET stripe_customer_id = EXCLUDED.stripe_customer_id
        """),
        {"user_id": user_id, "cust": stripe_customer_id}
    )

def upsert_subscription_from_stripe(db: Session, *, sub: Dict[str, Any], user_id: str) -> None:
    """
    subscriptions(
      id text PK,
      created_at timestamptz DEFAULT now(),
      user_id uuid,
      price_id text,
      status text,
      quantity bigint,
      cancel_at_period_end boolean,
      current_period_start timestamptz,
      current_period_end timestamptz,
      canceled_at timestamptz,
      trial_start timestamptz,
      trial_end timestamptz,
      metadata jsonb
    )
    We set created_at from Stripe's `sub.created`.
    """
    price_id = None
    items = sub.get("items", {}).get("data") or []
    if items:
        price = items[0].get("price") or {}
        price_id = price.get("id")
        cps = _ts(items[0].get("current_period_start"))
        cpe = _ts(items[0].get("current_period_end"))

    # Stripe timestamps (seconds since epoch, UTC)
    created_at = _ts(sub.get("created"))
    canceled_at = _ts(sub.get("canceled_at"))
    trial_start = _ts(sub.get("trial_start"))
    trial_end = _ts(sub.get("trial_end"))
    metadata = dict(sub.get("metadata") or {})  # Stripe metadata is dict[str,str]
    metadata_json = json.dumps(metadata)

    db.execute(
        text("""
            INSERT INTO subscriptions (
                id, created_at, user_id, price_id, status, quantity,
                cancel_at_period_end, current_period_start, current_period_end,
                canceled_at, trial_start, trial_end, metadata
            )
            VALUES (
                :id, :created_at, :user_id, :price_id, :status, :quantity,
                :cap_end, :cps, :cpe, :canceled_at, :trial_start, :trial_end, :metadata
            )
            ON CONFLICT (id) DO UPDATE SET
                user_id               = EXCLUDED.user_id,
                price_id              = EXCLUDED.price_id,
                status                = EXCLUDED.status,
                quantity              = EXCLUDED.quantity,
                cancel_at_period_end  = EXCLUDED.cancel_at_period_end,
                current_period_start  = EXCLUDED.current_period_start,
                current_period_end    = EXCLUDED.current_period_end,
                canceled_at           = EXCLUDED.canceled_at,
                trial_start           = EXCLUDED.trial_start,
                trial_end             = EXCLUDED.trial_end,
                metadata              = EXCLUDED.metadata
            -- NOTE: we intentionally do NOT update created_at on conflict
        """),
        {
            "id": sub["id"],
            "created_at": created_at,
            "user_id": user_id,
            "price_id": price_id,
            "status": sub.get("status"),
            "quantity": sub.get("quantity", 1),
            "cap_end": sub.get("cancel_at_period_end", False),
            "cps": cps,
            "cpe": cpe,
            "canceled_at": canceled_at,
            "trial_start": trial_start,
            "trial_end": trial_end,
            "metadata": metadata_json,
        }
    )

def commit(db: Session) -> None:
    db.commit()

def rollback(db: Session) -> None:
    db.rollback()

def user_id_from_customer(db: Session, stripe_customer_id: str) -> Optional[str]:
    row = db.execute(
        text("SELECT id FROM customers WHERE stripe_customer_id = :c"),
        {"c": stripe_customer_id}
    ).fetchone()
    return row[0] if row else None

def get_active_subscriptions_for_user(db: Session, user_id: str, exclude_id: Optional[str] = None) -> List[str]:
    """
    Return list of subscription ids for the user that are not cancelled and not equal to exclude_id.
    """
    if exclude_id:
        rows = db.execute(
            text("SELECT id FROM subscriptions WHERE user_id = :uid AND id != :ex AND status != 'canceled'"),
            {"uid": user_id, "ex": exclude_id}
        ).fetchall()
    else:
        rows = db.execute(
            text("SELECT id FROM subscriptions WHERE user_id = :uid AND status != 'canceled'"),
            {"uid": user_id}
        ).fetchall()
    return [r[0] for r in rows]

def mark_subscription_canceled(db: Session, subscription_id: str, canceled_at: Optional[datetime]) -> None:
    """
    Update subscription row to mark it cancelled. We set status='canceled' and canceled_at if provided.
    """
    db.execute(
        text("""
            UPDATE subscriptions
            SET status = 'canceled',
                canceled_at = :canceled_at
            WHERE id = :id
        """),
        {"id": subscription_id, "canceled_at": canceled_at}
    )
