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


def find_by_email(db: Session, email: str) -> Optional[Dict[str, Any]]:
    """
    Find a user by email address.
    
    Args:
        db: Database session
        email: Email address
    
    Returns:
        User dict or None if not found
    """
    logger.info(f"Finding user by email {email}")
    
    # TODO: Implement
    # from backend.app.models.user import User
    # user = db.query(User).filter(User.email == email).first()
    # return user.to_dict() if user else None
    
    raise NotImplementedError()


def save(db: Session, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new user.
    
    Args:
        db: Database session
        user_data: Dict containing user fields (email, name, etc.)
    
    Returns:
        Created user dict
    """
    logger.info(f"Creating new user with email {user_data.get('email')}")
    
    # TODO: Implement
    # from backend.app.models.user import User
    # user = User(**user_data)
    # db.add(user)
    # db.commit()
    # db.refresh(user)
    # return user.to_dict()
    
    raise NotImplementedError()


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


def delete(db: Session, user_id: UUID) -> bool:
    """
    Delete a user (soft or hard delete depending on requirements).
    
    Args:
        db: Database session
        user_id: UUID of the user
    
    Returns:
        True if deleted, False if not found
    """
    logger.info(f"Deleting user {user_id}")
    
    # TODO: Implement
    # from backend.app.models.user import User
    # user = db.query(User).filter(User.id == user_id).first()
    # if user:
    #     db.delete(user)  # or user.is_deleted = True for soft delete
    #     db.commit()
    #     return True
    # return False
    
    raise NotImplementedError()


def count_all(db: Session) -> int:
    """
    Count all users in the system (admin/analytics).
    
    Args:
        db: Database session
    
    Returns:
        Total number of users
    """
    # TODO: Implement
    # from backend.app.models.user import User
    # return db.query(User).count()
    
    raise NotImplementedError()
