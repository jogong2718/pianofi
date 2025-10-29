"""
User Repository - Data access for users table.

Used by: UserService, JobService (quota checks), PaymentService
Table: users or profiles
"""

from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


def find_by_id(db: Session, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Find a user by ID.
    
    Args:
        db: Database session
        user_id: ID of the user (string)
    
    Returns:
        User dict or None if not found
    """
    from sqlalchemy import text
    
    logger.info(f"Finding user {user_id}")
    
    user_sql = text("""
        SELECT id, first_name, last_name, created_at
        FROM users 
        WHERE id = :user_id
    """)
    
    user_result = db.execute(user_sql, {"user_id": user_id})
    user_row = user_result.fetchone()
    
    if user_row:
        return {
            "id": str(user_row[0]),
            "first_name": user_row[1],
            "last_name": user_row[2],
            "created_at": user_row[3]
        }
    
    return None



def update(db: Session, user_id: str, updates: Dict[str, Any]) -> int:
    """
    Update user fields.
    
    Args:
        db: Database session
        user_id: ID of the user (string)
        updates: Dict of fields to update
    
    Returns:
        Number of rows updated (0 if user not found)
    """
    from sqlalchemy import text
    
    logger.info(f"Updating user {user_id} with {updates}")
    
    update_sql = text("""
        UPDATE users 
        SET first_name = :first_name, last_name = :last_name
        WHERE id = :user_id
    """)
    
    result = db.execute(update_sql, {
        "first_name": updates.get("first_name"),
        "last_name": updates.get("last_name"),
        "user_id": user_id
    })
    
    logger.info(f"Update/Insert affected {result.rowcount} rows")
    return result.rowcount

