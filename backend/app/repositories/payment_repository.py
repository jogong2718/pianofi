"""
Payment Repository - Data access for payments and subscriptions tables.

Used by: PaymentService, AnalyticsService
Tables: payments, subscriptions
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)



def get_active_subscription(db: Session, user_id: str) -> Optional[Dict[str, Any]]:
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

