"""
Job Repository - Data access for jobs table.

Used by: JobService, AnalyticsService
Table: jobs
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


def save(db: Session, job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert a new job into the database.
    
    Args:
        db: Database session
        job_data: Dict containing job fields (user_id, audio_url, status, etc.)
    
    Returns:
        Dict representing the saved job with id
    
    Raises:
        DatabaseError: Insert failed
    """
    logger.info(f"Saving new job for user {job_data.get('user_id')}")
    
    # TODO: Implement
    # from backend.app.models.job import Job
    # job = Job(**job_data)
    # db.add(job)
    # db.commit()
    # db.refresh(job)
    # return job.to_dict()
    
    raise NotImplementedError("Move DB logic from router here")


def find_by_id(db: Session, job_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Find a job by its ID.
    
    Args:
        db: Database session
        job_id: UUID of the job
    
    Returns:
        Dict representing the job, or None if not found
    """
    logger.info(f"Finding job {job_id}")
    
    # TODO: Implement
    # from backend.app.models.job import Job
    # job = db.query(Job).filter(Job.id == job_id).first()
    # return job.to_dict() if job else None
    
    raise NotImplementedError()


def find_by_user_id(
    db: Session,
    user_id: UUID,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Find all jobs for a specific user with optional filters.
    
    Args:
        db: Database session
        user_id: UUID of the user
        filters: Optional dict with keys like "status", "created_after", etc.
        limit: Maximum number of jobs to return
        offset: Pagination offset
    
    Returns:
        List of job dicts
    """
    logger.info(f"Finding jobs for user {user_id} with filters {filters}")
    
    # TODO: Implement
    # from backend.app.models.job import Job
    # query = db.query(Job).filter(Job.user_id == user_id)
    # if filters:
    #     if "status" in filters:
    #         query = query.filter(Job.status == filters["status"])
    #     if "created_after" in filters:
    #         query = query.filter(Job.created_at >= filters["created_after"])
    # jobs = query.limit(limit).offset(offset).all()
    # return [job.to_dict() for job in jobs]
    
    raise NotImplementedError()


def update(db: Session, job_id: UUID, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a job's fields.
    
    Args:
        db: Database session
        job_id: UUID of the job to update
        updates: Dict of fields to update
    
    Returns:
        Updated job dict
    
    Raises:
        NotFoundError: Job not found
    """
    logger.info(f"Updating job {job_id} with {updates}")
    
    # TODO: Implement
    # from backend.app.models.job import Job
    # job = db.query(Job).filter(Job.id == job_id).first()
    # if not job:
    #     raise NotFoundError(f"Job {job_id} not found")
    # for key, value in updates.items():
    #     setattr(job, key, value)
    # db.commit()
    # db.refresh(job)
    # return job.to_dict()
    
    raise NotImplementedError()


def delete(db: Session, job_id: UUID) -> bool:
    """
    Delete a job from the database.
    
    Args:
        db: Database session
        job_id: UUID of the job to delete
    
    Returns:
        True if deleted, False if not found
    """
    logger.info(f"Deleting job {job_id}")
    
    # TODO: Implement
    # from backend.app.models.job import Job
    # job = db.query(Job).filter(Job.id == job_id).first()
    # if job:
    #     db.delete(job)
    #     db.commit()
    #     return True
    # return False
    
    raise NotImplementedError()


def count_by_user_id(db: Session, user_id: UUID) -> int:
    """
    Count total jobs for a user.
    
    Args:
        db: Database session
        user_id: UUID of the user
    
    Returns:
        Total number of jobs
    """
    logger.info(f"Counting jobs for user {user_id}")
    
    # TODO: Implement
    # from backend.app.models.job import Job
    # return db.query(Job).filter(Job.user_id == user_id).count()
    
    raise NotImplementedError()


def find_by_status(db: Session, status: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Find jobs by status (useful for background workers).
    
    Args:
        db: Database session
        status: Job status (pending, processing, completed, failed)
        limit: Maximum number of jobs to return
    
    Returns:
        List of job dicts
    """
    logger.info(f"Finding jobs with status {status}")
    
    # TODO: Implement
    # from backend.app.models.job import Job
    # jobs = db.query(Job).filter(Job.status == status).limit(limit).all()
    # return [job.to_dict() for job in jobs]
    
    raise NotImplementedError()


def count_all(db: Session) -> int:
    """
    Count all jobs in the system (admin/analytics).
    
    Args:
        db: Database session
    
    Returns:
        Total number of jobs
    """
    # TODO: Implement
    # from backend.app.models.job import Job
    # return db.query(Job).count()
    
    raise NotImplementedError()


# ========================================
# Functions for createJob.py (queue job)
# ========================================

def check_job_exists_for_user(db: Session, job_id: str, user_id: str) -> bool:
    """
    Check if a job exists and belongs to the specified user.
    Used for permission checks before queueing job.
    
    Args:
        db: Database session
        job_id: Job ID to check
        user_id: User ID for ownership verification
    
    Returns:
        True if job exists and belongs to user, False otherwise
    """
    from sqlalchemy import text
    
    logger.info(f"Checking if job {job_id} exists for user {user_id}")
    
    sql = text("""
        SELECT EXISTS(SELECT 1 FROM jobs 
                     WHERE job_id = :jobId AND user_id = :userId)
    """)
    
    result = db.execute(sql, {"jobId": job_id, "userId": user_id}).fetchone()
    return result[0] if result else False


def update_job_to_queued(
    db: Session, 
    job_id: str, 
    file_key: str, 
    model: str, 
    level: int
) -> int:
    """
    Update job status to 'queued' and set model, level, queued_at timestamp.
    
    Args:
        db: Database session
        job_id: Job ID to update
        file_key: File key for additional validation
        model: Model name ('amt' or 'picogen')
        level: Processing level (1-3)
    
    Returns:
        Number of rows affected (0 if job not found or file_key mismatch)
    """
    from sqlalchemy import text
    
    logger.info(f"Updating job {job_id} to queued status with model={model}, level={level}")
    
    sql = text("""
        UPDATE jobs
        SET status = 'queued', queued_at = NOW(), model = :model, level = :level
        WHERE job_id = :jobId AND file_key = :fileKey
    """)
    
    result = db.execute(sql, {
        "jobId": job_id,
        "fileKey": file_key,
        "model": model,
        "level": level
    })
    
    return result.rowcount


# ========================================
# Functions for createSheetMusic.py (download files)
# ========================================

def get_job_status_for_user(db: Session, job_id: str, user_id: str) -> Optional[str]:
    """
    Get job status if job exists and belongs to user.
    Used for sheet music download endpoints.
    
    Args:
        db: Database session
        job_id: Job ID
        user_id: User ID for ownership verification
    
    Returns:
        Job status string, or None if not found/access denied
    """
    from sqlalchemy import text
    
    logger.info(f"Getting job status for job {job_id}, user {user_id}")
    
    sql = text("""
        SELECT status FROM jobs 
        WHERE job_id = :job_id AND user_id = :user_id
    """)
    
    result = db.execute(sql, {"job_id": job_id, "user_id": user_id}).fetchone()
    return result[0] if result else None


def get_job_status_with_audio_metadata(
    db: Session, 
    job_id: str, 
    user_id: str
) -> Optional[tuple[str, Optional[dict]]]:
    """
    Get job status and audio metadata if job exists and belongs to user.
    Used for audio download endpoint.
    
    Args:
        db: Database session
        job_id: Job ID
        user_id: User ID for ownership verification
    
    Returns:
        Tuple of (status, audio_metadata), or None if not found/access denied
    """
    from sqlalchemy import text
    
    logger.info(f"Getting job status and audio metadata for job {job_id}, user {user_id}")
    
    sql = text("""
        SELECT status, audio_metadata FROM jobs 
        WHERE job_id = :job_id AND user_id = :user_id
    """)
    
    result = db.execute(sql, {"job_id": job_id, "user_id": user_id}).fetchone()
    return (result[0], result[1]) if result else None
