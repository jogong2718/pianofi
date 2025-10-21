"""
User Service - Handles user profile management.

Functions for profile updates, settings, and quota management.
Serves routers: updateProfile
"""

from typing import Dict, Any, Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


def get_profile(user_id: UUID, user_repository) -> Dict[str, Any]:
    """
    Get user profile information.
    
    Args:
        user_id: UUID of the user
        user_repository: Repository for user data access
    
    Returns:
        Dict containing user profile data
    
    Raises:
        NotFoundError: User not found
    """
    logger.info(f"Fetching profile for user {user_id}")
    
    # TODO: Implement
    # user = user_repository.find_by_id(user_id)
    # if not user:
    #     raise NotFoundError(f"User {user_id} not found")
    # return user.to_dict()
    
    raise NotImplementedError()


def update_profile(
    user_id: str,
    first_name: str,
    last_name: str,
    email: str,
    db,
    user_repository
) -> Dict[str, Any]:
    """
    Update user profile information.
    
    Args:
        user_id: ID of the user (string)
        first_name: New first name
        last_name: New last name
        email: User email (from JWT token, for response)
        db: Database session
        user_repository: Repository for user data access
    
    Returns:
        Dict with success, message, and user data
    
    Raises:
        HTTPException: If user not found
    """
    import logging
    from fastapi import HTTPException
    
    logger.info(f"Updating profile for user {user_id}")
    
    # 1. Update database (but don't commit yet)
    result = user_repository.update(db, user_id, {
        "first_name": first_name,
        "last_name": last_name
    })
    
    if result == 0:
        db.rollback()
        raise HTTPException(status_code=404, detail="User not found")
    
    db.commit()
    
    # 2. Fetch updated user
    user_row = user_repository.find_by_id(db, user_id)
    
    user_data = {
        "id": user_row["id"],
        "first_name": user_row["first_name"],
        "last_name": user_row["last_name"],
        "created_at": user_row["created_at"].isoformat() if user_row["created_at"] else None,
        "email": email
    }
    
    logging.info(f"Profile updated for user {user_id}")
    
    return {
        "success": True,
        "message": "Profile updated successfully",
        "user": user_data
    }


def update_notification_settings(
    user_id: UUID,
    settings: Dict[str, bool],
    user_repository
) -> Dict[str, Any]:
    """
    Update user notification preferences.
    
    Args:
        user_id: UUID of the user
        settings: Dict of notification settings (email_on_complete, etc.)
        user_repository: Repository for user data access
    
    Returns:
        Updated notification settings
    """
    logger.info(f"Updating notification settings for user {user_id}")
    
    # TODO: Implement
    # validated_settings = _validate_notification_settings(settings)
    # user_repository.update(user_id, {"notification_settings": validated_settings})
    
    raise NotImplementedError()


def get_user_quota(user_id: UUID, user_repository, job_repository) -> Dict[str, Any]:
    """
    Get user's current usage and quota limits.
    
    Args:
        user_id: UUID of the user
        user_repository: Repository for user data access
        job_repository: Repository for job data access
    
    Returns:
        Dict containing:
            - jobs_used: Number of jobs used this period
            - jobs_limit: Maximum jobs allowed
            - storage_used_mb: Storage used in MB
            - storage_limit_mb: Storage limit in MB
            - reset_date: When quota resets (for free tier)
    """
    logger.info(f"Getting quota for user {user_id}")
    
    # TODO: Implement
    # user = user_repository.find_by_id(user_id)
    # job_count = job_repository.count_by_user_id(user_id)
    # return {
    #     "jobs_used": job_count,
    #     "jobs_limit": user.job_quota,
    #     ...
    # }
    
    raise NotImplementedError()


def check_quota_available(
    user_id: UUID,
    required_jobs: int,
    user_repository,
    job_repository
) -> bool:
    """
    Check if user has quota available for new jobs.
    
    Args:
        user_id: UUID of the user
        required_jobs: Number of jobs user wants to create
        user_repository: Repository for user data access
        job_repository: Repository for job data access
    
    Returns:
        True if quota available, False otherwise
    """
    logger.info(f"Checking quota for user {user_id}")
    
    # TODO: Implement
    # quota = get_user_quota(user_id, user_repository, job_repository)
    # return quota["jobs_used"] + required_jobs <= quota["jobs_limit"]
    
    raise NotImplementedError()
