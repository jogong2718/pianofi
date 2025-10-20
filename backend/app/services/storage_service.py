"""
Storage Service - Handles file storage operations (S3).

Functions for upload/download URL generation and file management.
Serves routers: uploadUrl, getDownload
"""

from typing import Optional, Dict, Any
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


def generate_upload_url(
    user_id: UUID,
    filename: str,
    content_type: Optional[str],
    max_size_mb: int,
    s3_client,
    file_repository=None
) -> Dict[str, Any]:
    """
    Generate a presigned URL for uploading a file to S3.
    
    Business logic:
    1. Validate filename and content type
    2. Generate unique S3 key
    3. Create presigned POST URL with size/type constraints
    4. Optionally track file metadata in DB
    
    Args:
        user_id: UUID of the user uploading
        filename: Original filename
        content_type: MIME type (e.g., audio/mpeg, audio/wav)
        max_size_mb: Maximum allowed file size in MB
        s3_client: Client for S3 operations
        file_repository: Optional repository for tracking file metadata
    
    Returns:
        Dict containing:
            - upload_url: Presigned URL for upload
            - fields: Form fields for POST request
            - file_key: S3 key where file will be stored
            - expires_in: Seconds until URL expires
    
    Raises:
        ValidationError: Invalid filename or content type
        StorageError: S3 operation failed
    """
    logger.info(f"Generating upload URL for user {user_id}, file {filename}")
    
    # TODO: Implement
    # 1. Validate filename extension (allow .mp3, .wav, .flac, etc.)
    # 2. Generate S3 key: f"uploads/{user_id}/{uuid4()}/{filename}"
    # 3. Create presigned POST: s3_client.generate_presigned_post(...)
    # 4. Track in DB if file_repository exists
    
    raise NotImplementedError("Upload URL logic to be moved from router")


def generate_download_url(
    file_key: str,
    user_id: UUID,
    expiry_seconds: int,
    s3_client,
    file_repository=None
) -> str:
    """
    Generate a presigned URL for downloading a file from S3.
    
    Business logic:
    1. Verify user has access to this file
    2. Check file exists in S3
    3. Generate presigned GET URL
    
    Args:
        file_key: S3 key of the file
        user_id: UUID of the requesting user (for authorization)
        expiry_seconds: URL expiry time in seconds
        s3_client: Client for S3 operations
        file_repository: Optional repository for checking ownership
    
    Returns:
        Presigned download URL (string)
    
    Raises:
        NotFoundError: File not found in S3
        UnauthorizedError: User doesn't have access to this file
        StorageError: S3 operation failed
    """
    logger.info(f"Generating download URL for file {file_key}, user {user_id}")
    
    # TODO: Implement
    # 1. Verify ownership/access
    # 2. Check file exists: s3_client.head_object(bucket, file_key)
    # 3. Generate presigned URL: s3_client.generate_presigned_url('get_object', ...)
    
    raise NotImplementedError("Download URL logic to be moved from router")


def delete_file(file_key: str, user_id: UUID, s3_client, file_repository=None) -> bool:
    """
    Delete a file from S3.
    
    Args:
        file_key: S3 key of the file to delete
        user_id: UUID of the requesting user (for authorization)
        s3_client: Client for S3 operations
        file_repository: Optional repository for metadata cleanup
    
    Returns:
        True if deleted successfully
    
    Raises:
        UnauthorizedError: User doesn't have access to this file
    """
    logger.info(f"Deleting file {file_key} for user {user_id}")
    
    # TODO: Implement
    # 1. Verify ownership
    # 2. Delete from S3: s3_client.delete_object(bucket, file_key)
    # 3. Delete metadata if tracked: file_repository.delete_by_key(file_key)
    
    raise NotImplementedError()


def delete_job_files(job_id: UUID, s3_client, file_repository=None) -> None:
    """
    Delete all files associated with a job.
    
    Args:
        job_id: UUID of the job
        s3_client: Client for S3 operations
        file_repository: Optional repository for finding files
    """
    logger.info(f"Deleting all files for job {job_id}")
    
    # TODO: Implement
    # 1. List all files for job (from DB or S3 prefix)
    # 2. Delete each file
    
    raise NotImplementedError()


def validate_file_type(filename: str, allowed_extensions: Optional[list] = None) -> bool:
    """
    Validate file type by extension.
    
    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions (default: audio formats)
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: Invalid file type
    """
    if allowed_extensions is None:
        allowed_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac']
    
    # TODO: Implement validation logic
    raise NotImplementedError()
