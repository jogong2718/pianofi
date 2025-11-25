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
        job_data: Dict containing job fields (job_id, file_key, user_id, status, etc.)
    
    Returns:
        Dict representing the saved job with id
    
    Raises:
        DatabaseError: Insert failed
    """
    logger.info(f"Saving new job for user {job_data.get('user_id')}")
    
    from sqlalchemy import text
    
    sql = text("""
        INSERT INTO jobs (job_id, file_key, status, user_id, file_name, file_size, file_duration)
        VALUES (:job_id, :file_key, :status, :user_id, :file_name, :file_size, :file_duration)
        RETURNING job_id, file_key, status, user_id, file_name, file_size, file_duration, created_at
    """)
    
    result = db.execute(sql, job_data)
    row = result.fetchone()
    
    if row:
        return {
            "job_id": str(row[0]),
            "file_key": row[1],
            "status": row[2],
            "user_id": str(row[3]),
            "file_name": row[4],
            "file_size": row[5],
            "file_duration": row[6],
            "created_at": row[7]
        }
    
    raise Exception("Failed to save job")


def find_by_user_id(
    db: Session,
    user_id: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Find all jobs for a specific user with optional filters.
    
    Args:
        db: Database session
        user_id: ID of the user (string)
        filters: Optional dict with keys like "status", "created_after", etc.
        limit: Maximum number of jobs to return
        offset: Pagination offset
    
    Returns:
        List of job dicts
    """
    from sqlalchemy import text
    
    logger.info(f"Finding jobs for user {user_id} with filters {filters}")
    
    sql = text("""
        SELECT 
            job_id,
            file_name,
            file_size,
            status,
            created_at,
            queued_at,
            started_at,
            finished_at,
            model,
            level
        FROM jobs 
        WHERE user_id = :user_id
        AND status != 'deleted' 
        ORDER BY created_at DESC
    """)
    
    result = db.execute(sql, {"user_id": user_id})
    jobs = result.fetchall()
    
    # Convert to list of dictionaries
    jobs_list = []
    for job in jobs:
        job_dict = {
            "job_id": str(job.job_id),
            "file_name": job.file_name,
            "file_size": job.file_size,
            "status": job.status,
            "created_at": job.created_at,
            "queued_at": job.queued_at,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "model": job.model,
            "level": job.level
        }
        jobs_list.append(job_dict)
    
    return jobs_list


def update(db: Session, job_id: str, user_id: str, updates: Dict[str, Any]) -> int:
    """
    Update a job's fields (with user ownership check).
    
    Args:
        db: Database session
        job_id: ID of the job to update
        user_id: ID of the user (for authorization)
        updates: Dict of fields to update
    
    Returns:
        Number of rows updated (0 if not found or access denied)
    """
    from sqlalchemy import text
    
    logger.info(f"Updating job {job_id} with {updates}")
    
    update_sql = text("""
        UPDATE jobs 
        SET file_name = :file_name
        WHERE job_id = :job_id AND user_id = :user_id
    """)
    
    result = db.execute(update_sql, {
        "file_name": updates.get("file_name"),
        "job_id": job_id,
        "user_id": user_id
    })
    
    return result.rowcount


def delete(db: Session, job_id: str, user_id: str) -> Optional[str]:
    """
    Soft delete a job by setting status to 'deleted'.
    
    Args:
        db: Database session
        job_id: ID of the job to delete
        user_id: User ID for ownership verification
    
    Returns:
        Job ID if deleted successfully, None if not found or access denied
    """
    from sqlalchemy import text
    
    logger.info(f"Soft deleting job {job_id} for user {user_id}")
    
    sql = text("""
        UPDATE jobs 
        SET status = 'deleted'
        WHERE job_id = :job_id AND user_id = :user_id
        RETURNING job_id
    """)
    
    result = db.execute(sql, {"job_id": job_id, "user_id": user_id})
    deleted_job = result.fetchone()
    
    return str(deleted_job[0]) if deleted_job else None


def count_by_user_id(db: Session, user_id: str) -> int:
    """
    Count total jobs for a user.
    
    Args:
        db: Database session
        user_id: ID of the user (string)
    
    Returns:
        Total number of jobs
    """
    from sqlalchemy import text
    
    logger.info(f"Counting jobs for user {user_id}")
    
    sql = text("SELECT COUNT(*) FROM jobs WHERE user_id = :user_id")
    result = db.execute(sql, {"user_id": user_id})
    return result.scalar()


def count_by_user_id_and_status(db: Session, user_id: str, statuses: List[str]) -> int:
    """
    Count jobs for a user with specific statuses.
    
    Args:
        db: Database session
        user_id: ID of the user (string)
        statuses: List of status values to filter by
    
    Returns:
        Number of jobs matching the criteria
    """
    from sqlalchemy import text
    
    logger.info(f"Counting jobs for user {user_id} with statuses {statuses}")
    
    # Create placeholders for the IN clause
    status_placeholders = ", ".join([f":status_{i}" for i in range(len(statuses))])
    sql = text(f"SELECT COUNT(*) FROM jobs WHERE user_id = :user_id AND status IN ({status_placeholders})")
    
    # Build parameters dict
    params = {"user_id": user_id}
    for i, status in enumerate(statuses):
        params[f"status_{i}"] = status
    
    result = db.execute(sql, params)
    return result.scalar()


def count_by_user_id_since_date(db: Session, user_id: str, start_date) -> int:
    """
    Count jobs for a user created since a specific date.
    
    Args:
        db: Database session
        user_id: ID of the user (string)
        start_date: Start date for the count
    
    Returns:
        Number of jobs created since start_date
    """
    from sqlalchemy import text
    
    logger.info(f"Counting jobs for user {user_id} since {start_date}")
    
    sql = text("SELECT COUNT(*) FROM jobs WHERE user_id = :user_id AND created_at >= :start_date")
    result = db.execute(sql, {"user_id": user_id, "start_date": start_date})
    return result.scalar()


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
        model: Model name ('amt' or 'picogen' or 'basicpitch')
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

# ========================================
# Functions for getDashboardMetrics.py
# ========================================

def count_model_usage_since_date(
    db: Session,
    user_id: str,
    model: str,
    start_date
) -> int:
    """
    Count how many times a specific model was used by a user since a given date.
    
    Args:
        db: Database session
        user_id: ID of the user (string)
        model: Model name to filter by (e.g., 'picogen')
        start_date: Start date for the count
    
    Returns:
        Number of times the model was used since start_date
    """
    from sqlalchemy import text
    
    logger.info(f"Counting usage of model {model} for user {user_id} since {start_date}")
    
    sql = text("""
        SELECT COUNT(*) FROM jobs 
        WHERE user_id = :user_id 
        AND model = :model 
        AND created_at >= :start_date
    """)
    
    result = db.execute(sql, {
        "user_id": user_id,
        "model": model,
        "start_date": start_date
    })
    
    return result.scalar()