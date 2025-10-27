"""
Job Service - Handles all job-related business logic.

Functions for job creation, retrieval, updates, and deletion.
Serves routers: createJob, getUserJobs, updateJob, deleteJob
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
import json
import time
from app.repositories import job_repository
from app.config_loader import Config

logger = logging.getLogger(__name__)


def create_job(
    user_id: UUID,
    audio_url: str,
    options: Optional[Dict[str, Any]],
    job_repository,
    user_repository,
    storage_service,
    task_queue
) -> Dict[str, Any]:
    """
    Create a new transcription job.
    
    Business logic:
    1. Validate user quota
    2. Validate audio URL and options
    3. Create job record in database
    4. Enqueue background transcription task
    5. Return job details
    
    Args:
        user_id: UUID of the user creating the job
        audio_url: S3 URL or presigned URL of the audio file
        options: Optional job configuration (model, tempo, etc.)
        job_repository: Repository for job data access
        user_repository: Repository for user data access
        storage_service: Service for file storage operations
        task_queue: Queue for background job processing
    
    Returns:
        Dict containing job details (id, status, created_at, etc.)
    
    Raises:
        QuotaExceeded: User has reached their job limit
        ValidationError: Invalid audio URL or options
        StorageError: Audio file not accessible
    """
    logger.info(f"Creating job for user {user_id}")
    
    # TODO: Implement business logic
    # 1. Check user quota: job_count = job_repository.count_by_user_id(user_id)
    # 2. Validate options
    # 3. Create job: job = job_repository.save(Job(...))
    # 4. Enqueue: task_queue.enqueue_transcription_job(job.id)
    # 5. Return job details
    
    raise NotImplementedError("Create job logic to be moved from router")


def get_user_jobs(
    user_id: str,
    db,
    job_repository
) -> List[Dict[str, Any]]:
    """
    Retrieve jobs for a user.
    
    Args:
        user_id: ID of the user (string)
        db: Database session
        job_repository: Repository for job data access
    
    Returns:
        List of job dictionaries with formatted timestamps
    """
    logger.info(f"Fetching jobs for user {user_id}")
    
    # Fetch jobs from repository
    jobs = job_repository.find_by_user_id(db, user_id)
    
    # Format timestamps to ISO format
    jobs_list = []
    for job in jobs:
        job_dict = {
            "job_id": job["job_id"],
            "file_name": job["file_name"],
            "file_size": job["file_size"],
            "status": job["status"],
            "created_at": job["created_at"].isoformat() if job["created_at"] else None,
            "queued_at": job["queued_at"].isoformat() if job["queued_at"] else None,
            "started_at": job["started_at"].isoformat() if job["started_at"] else None,
            "finished_at": job["finished_at"].isoformat() if job["finished_at"] else None,
            "model": job["model"],
            "level": job["level"]
        }
        jobs_list.append(job_dict)
    
    logger.info(f"Found {len(jobs_list)} jobs for user {user_id}")
    return jobs_list


def get_job_by_id(job_id: UUID, user_id: UUID, job_repository) -> Dict[str, Any]:
    """
    Get a specific job by ID with ownership verification.
    
    Args:
        job_id: UUID of the job
        user_id: UUID of the requesting user (for authorization)
        job_repository: Repository for job data access
    
    Returns:
        Job details dictionary
    
    Raises:
        NotFoundError: Job not found
        UnauthorizedError: User doesn't own this job
    """
    logger.info(f"Fetching job {job_id} for user {user_id}")
    
    # TODO: Implement
    # job = job_repository.find_by_id(job_id)
    # if not job:
    #     raise NotFoundError(f"Job {job_id} not found")
    # if job.user_id != user_id:
    #     raise UnauthorizedError("Access denied")
    # return job.to_dict()
    
    raise NotImplementedError()


def update_job(
    job_id: str,
    user_id: str,
    file_name: str,
    db,
    job_repository
) -> Dict[str, Any]:
    """
    Update a job's file_name.
    
    Args:
        job_id: ID of the job to update
        user_id: ID of the requesting user (for authorization)
        file_name: New file name
        db: Database session
        job_repository: Repository for job data access
    
    Returns:
        Dict with success and message
    
    Raises:
        HTTPException: If job not found or access denied
    """
    from fastapi import HTTPException
    
    logger.info(f"Updating job {job_id} for user {user_id}")
    
    # Update job with ownership check
    result = job_repository.update(db, job_id, user_id, {
        "file_name": file_name
    })
    
    if result == 0:
        db.rollback()
        raise HTTPException(status_code=404, detail="Job not found or access denied")
    
    db.commit()
    
    return {
        "success": True,
        "message": "Job updated successfully"
    }


def delete_job(job_id: str, user_id: str, db) -> Dict[str, Any]:
    """
    Soft delete a job by setting status to 'deleted'.
    
    Business logic:
    1. Verify ownership and delete job (atomic operation in repository)
    2. Return success message
    
    Args:
        job_id: ID of the job to delete
        user_id: ID of the requesting user (for authorization)
        db: Database session
    
    Returns:
        Dict with message and jobId
    
    Raises:
        PermissionError: Job not found or access denied
    """
    from app.repositories import job_repository
    
    logger.info(f"Deleting job {job_id} for user {user_id}")
    
    # Call repository to soft delete
    deleted_job_id = job_repository.delete(db, job_id, user_id)
    
    if not deleted_job_id:
        raise PermissionError("Job not found or access denied")
    
    return {
        "message": "Job successfully deleted",
        "jobId": deleted_job_id
    }


def update_job_status(
    job_id: UUID,
    status: str,
    error_message: Optional[str],
    job_repository
) -> None:
    """
    Update job status (typically called by background workers).
    
    Args:
        job_id: UUID of the job
        status: New status (processing, completed, failed)
        error_message: Optional error message if status is failed
        job_repository: Repository for job data access
    """
    logger.info(f"Updating job {job_id} status to {status}")
    
    # TODO: Implement
    # updates = {"status": status}
    # if error_message:
    #     updates["error_message"] = error_message
    # job_repository.update(job_id, updates)
    # _notify_user_of_status_change(job_id, status)
    
    raise NotImplementedError()


# ========================================
# Functions for createJob.py (queue job)
# ========================================

def get_queue_name(model: str, environment: str) -> str:
    """Get Redis queue name for model and environment."""
    queue_map = {
        ("picogen", "production"): "picogen_job_queue_prod",
        ("picogen", "development"): "picogen_job_queue_dev",
        ("amt", "production"): "amt_job_queue_prod",
        ("amt", "development"): "amt_job_queue_dev",
    }
    queue_name = queue_map.get((model, environment))
    if not queue_name:
        raise ValueError(f"Invalid model '{model}' or environment '{environment}'")
    return queue_name

def queue_job(
    job_id: str,
    file_key: str,
    user_id: str,
    model: str,
    level: int,
    db,
    redis_client
) -> Dict[str, Any]:
    """
    Queue an existing job for processing.
    
    Business logic:
    1. Validate job_id and file_key are provided
    2. Check job exists and belongs to user (permission check)
    3. Update job status to 'queued' in database
    4. Push job to appropriate Redis queue (amt or picogen)
    
    Args:
        job_id: ID of the job to queue
        file_key: File key for validation
        user_id: ID of the user (for permission check)
        model: Model to use ('amt' or 'picogen')
        level: Processing level (1-3)
        db: Database session
        redis_client: Redis client for queue operations
    
    Returns:
        Dict with success status
    
    Raises:
        ValueError: Missing required fields
        PermissionError: Job not found or access denied
        RuntimeError: Update failed or queue operation failed
    """
    logger.info(f"Queueing job {job_id} for user {user_id} with model={model}")
    
    # 1. Validate inputs
    if not job_id or not file_key:
        raise ValueError("jobId and fileKey are required")
    
    # 2. Check permission (job exists and belongs to user)
    job_exists = job_repository.check_job_exists_for_user(db, job_id, user_id)
    if not job_exists:
        raise PermissionError("Job not found or access denied")
    
    # 3. Update job status to 'queued' in database
    rows_updated = job_repository.update_job_to_queued(
        db, job_id, file_key, model, level
    )
    
    if rows_updated == 0:
        raise RuntimeError("Job not found or fileKey mismatch")
    
    # Commit database changes
    db.commit()
    
    # 4. Push job to Redis queue
    job_data = {
        "jobId": job_id,
        "fileKey": file_key,
        "userId": user_id,
        "createdAt": time.time(),
        "model": model,
        "level": level
    }
    
    # Route to correct queue based on model
    queue_name = get_queue_name(model, Config.ENVIRONMENT)
    
    redis_client.lpush(queue_name, json.dumps(job_data))
    logger.info(f"Job {job_id} pushed to {queue_name}")
    
    return {"success": True}

