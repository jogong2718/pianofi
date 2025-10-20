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


def find_by_id(db: Session, user_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Find a user by ID.
    
    Args:
        db: Database session
        user_id: UUID of the user
    
    Returns:
        User dict or None if not found
    """
    logger.info(f"Finding user {user_id}")
    
    # TODO: Implement
    # from backend.app.models.user import User
    # user = db.query(User).filter(User.id == user_id).first()
    # return user.to_dict() if user else None
    
    raise NotImplementedError()


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


def update(db: Session, user_id: UUID, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update user fields.
    
    Args:
        db: Database session
        user_id: UUID of the user
        updates: Dict of fields to update
    
    Returns:
        Updated user dict
    
    Raises:
        NotFoundError: User not found
    """
    logger.info(f"Updating user {user_id} with {updates}")
    
    # TODO: Implement
    # from backend.app.models.user import User
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     raise NotFoundError(f"User {user_id} not found")
    # for key, value in updates.items():
    #     setattr(user, key, value)
    # db.commit()
    # db.refresh(user)
    # return user.to_dict()
    
    raise NotImplementedError()


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
