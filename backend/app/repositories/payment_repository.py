"""
Payment Repository - Data access for payments and subscriptions tables.

Used by: PaymentService, AnalyticsService
Tables: prices, products, subscriptions, customers
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)



def get_active_subscription_limit(db: Session, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user's active subscription with monthly transcription limit.
    
    Args:
        db: Database session
        user_id: ID of the user (string)
    
    Returns:
        Subscription dict with monthly_transcription_limit or None if no active subscription
    """
    from sqlalchemy import text
    
    logger.info(f"Getting active subscription for user {user_id}")
    
    sql = text("""
        SELECT p.monthly_transcription_limit 
        FROM subscriptions s
        JOIN prices p ON s.price_id = p.id
        WHERE s.user_id = :user_id 
        AND s.status = 'active'
        ORDER BY s.created_at DESC
        LIMIT 1
    """)
    
    result = db.execute(sql, {"user_id": user_id})
    row = result.fetchone()
    
    if row:
        return {
            "monthly_transcription_limit": row[0]
        }
    
    return None

def find_user_stripe_customer_id(db: Session, user_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Find the Stripe customer ID for a user.
    
    Args:
        db: Database session
        user_id: UUID of the user
    
    Returns:
        Stripe customer ID or None if not found

    """
    from sqlalchemy import text
    
    logger.info(f"Finding Stripe customer ID for user {user_id}")
    
    stripe_sql = text("""
        SELECT stripe_customer_id
        FROM customers 
        WHERE id = :user_id
    """)
    
    result = db.execute(stripe_sql, {"user_id": str(user_id)})
    row = result.fetchone()
    
    if row:
        return {
            "user_id": str(user_id),
            "stripe_customer_id": row[0]
        }
    
    return None

def get_active_subscription_id(db: Session, user_id: str) -> Optional[str]:
    """
    Get the subscription ID for a user's active subscription.
    
    Args:
        db: Database session
        user_id: ID of the user (string)
    
    Returns:
        Subscription ID or None if no active subscription
    """
    from sqlalchemy import text
    
    logger.info(f"Getting active subscription ID for user {user_id}")
    
    sql = text("""
        SELECT id 
        FROM subscriptions
        WHERE user_id = :user_id 
        AND status = 'active'
        ORDER BY created_at DESC
        LIMIT 1
    """)
    
    result = db.execute(sql, {"user_id": user_id})
    row = result.fetchone()
    
    return row[0] if row else None