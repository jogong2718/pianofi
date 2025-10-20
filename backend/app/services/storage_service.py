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
    user_id: str,
    filename: str,
    file_size: int,
    content_type: str,
    s3_client,
    aws_creds: Dict[str, str],
    use_local: bool = False,
    local_upload_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a presigned URL for uploading a file to S3.
    
    Business logic:
    1. Validate filename, content type, and file size
    2. Generate unique job_id and S3 key
    3. Create presigned PUT URL
    4. Return upload URL, job_id, and file_key
    
    Args:
        user_id: ID of the user uploading
        filename: Original filename
        file_size: Size of file in bytes
        content_type: MIME type (e.g., audio/mpeg, audio/wav)
        s3_client: Client for S3 operations
        aws_creds: AWS credentials dict with s3_bucket
        use_local: Whether to use local storage
        local_upload_dir: Local directory for uploads (if use_local=True)
    
    Returns:
        Dict containing:
            - upload_url: Presigned URL for upload
            - job_id: Generated job ID
            - file_key: S3 key where file will be stored
    
    Raises:
        ValueError: Invalid file parameters
        Exception: S3 operation failed
    """
    import uuid
    from botocore.exceptions import ClientError
    
    logger.info(f"Generating upload URL for user {user_id}, file {filename}")
    
    # 1. Validate upload request
    validation_error = validate_upload_request(filename, file_size, content_type)
    if validation_error:
        raise ValueError(validation_error)
    
    # 2. Generate job_id and file_key
    job_id = str(uuid.uuid4())
    file_ext = '.' + filename.lower().split('.')[-1] if '.' in filename else '.mp3'
    file_key = f"mp3/{job_id}{file_ext}"
    
    # 3. Generate presigned URL
    if use_local:
        from pathlib import Path
        upload_dir = Path(local_upload_dir) if local_upload_dir else Path("uploads")
        upload_url = str(upload_dir / "mp3" / job_id)
    else:
        try:
            upload_url = s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": aws_creds["s3_bucket"],
                    "Key": file_key,
                    "ContentType": content_type
                },
                ExpiresIn=3600,
                HttpMethod="PUT",
            )
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise Exception(f"Could not generate presigned URL: {e}")
    
    return {
        "upload_url": upload_url,
        "job_id": job_id,
        "file_key": file_key
    }


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
    
    file_ext = '.' + filename.lower().split('.')[-1] if '.' in filename else ''
    return file_ext in allowed_extensions


def validate_upload_request(file_name: str, file_size: int, content_type: str) -> Optional[str]:
    """
    Validate upload parameters before generating pre-signed URL.
    
    Args:
        file_name: Name of the file
        file_size: Size in bytes
        content_type: MIME type
    
    Returns:
        Error message if invalid, None if valid
    """
    # File size validation (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    if file_size > MAX_FILE_SIZE:
        return f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
    
    # File extension validation
    ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.flac'}
    file_ext = '.' + file_name.lower().split('.')[-1] if '.' in file_name else ''
    if file_ext not in ALLOWED_EXTENSIONS:
        return f"Invalid file extension: {file_ext}"
    
    # MIME type validation
    ALLOWED_MIME_TYPES = {'audio/mpeg', 'audio/wav', 'audio/flac', 'audio/x-wav', 'audio/x-flac'}
    if content_type not in ALLOWED_MIME_TYPES:
        return f"Invalid file type: {content_type}"
    
    return None  # Valid
