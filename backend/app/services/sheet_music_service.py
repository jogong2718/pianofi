"""
Sheet Music Service - Handles sheet music generation and management.

Functions for generating, retrieving, and managing sheet music.
Serves routers: createSheetMusic
"""

from typing import Dict, Any, Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)



# ========================================
# Functions moved from createSheetMusic.py router
# ========================================


def get_xml_file(job_id: str, user_id: str, db, s3_client, aws_creds) -> bytes:
    """
    Download MusicXML file for a completed job.
    
    Business logic:
    1. Check job exists and belongs to user
    2. Check job status is 'done'
    3. Download XML file from S3
    
    Args:
        job_id: Job ID
        user_id: User ID for permission check
        db: Database session
        s3_client: Boto3 S3 client
        aws_creds: AWS credentials dict
    
    Returns:
        XML file bytes
    
    Raises:
        PermissionError: Job not found or access denied
        ValueError: Job not completed
        FileNotFoundError: File not found in S3
        RuntimeError: S3 download failed
    """
    from app.repositories import job_repository
    from botocore.exceptions import ClientError
    
    logger.info(f"Getting XML file for job {job_id}, user {user_id}")
    
    # 1. Check job status
    status = job_repository.get_job_status_for_user(db, job_id, user_id)
    
    if not status:
        raise PermissionError("Job not found or access denied")
    
    if status != 'done':
        raise ValueError(f"Job not completed. Current status: {status}")
    
    # 2. Download from S3
    s3_key = f"xml/{job_id}.musicxml"
    
    try:
        response = s3_client.get_object(
            Bucket=aws_creds["s3_bucket"],
            Key=s3_key
        )
        return response['Body'].read()
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.error(f"MusicXML file not found in S3: {s3_key}")
            raise FileNotFoundError("MusicXML file not found in S3")
        else:
            logger.error(f"S3 download failed: {str(e)}")
            raise RuntimeError(f"S3 download failed: {str(e)}")


def get_midi_file(job_id: str, user_id: str, db, s3_client, aws_creds) -> bytes:
    """
    Download MIDI file for a completed job.
    
    Business logic:
    1. Check job exists and belongs to user
    2. Check job status is 'done'
    3. Download MIDI file from S3
    
    Args:
        job_id: Job ID
        user_id: User ID for permission check
        db: Database session
        s3_client: Boto3 S3 client
        aws_creds: AWS credentials dict
    
    Returns:
        MIDI file bytes
    
    Raises:
        PermissionError: Job not found or access denied
        ValueError: Job not completed
        FileNotFoundError: File not found in S3
        RuntimeError: S3 download failed
    """
    from app.repositories import job_repository
    from botocore.exceptions import ClientError
    
    logger.info(f"Getting MIDI file for job {job_id}, user {user_id}")
    
    # 1. Check job status
    status = job_repository.get_job_status_for_user(db, job_id, user_id)
    
    if not status:
        raise PermissionError("Job not found or access denied")
    
    if status != 'done':
        raise ValueError(f"Job not completed. Current status: {status}")
    
    # 2. Download from S3
    s3_key = f"midi/{job_id}.mid"
    
    try:
        response = s3_client.get_object(
            Bucket=aws_creds["s3_bucket"],
            Key=s3_key
        )
        return response['Body'].read()
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.error(f"MIDI file not found in S3: {s3_key}")
            raise FileNotFoundError("MIDI file not found in S3")
        else:
            logger.error(f"S3 download failed: {str(e)}")
            raise RuntimeError(f"S3 download failed: {str(e)}")


def get_audio_file(job_id: str, user_id: str, db, s3_client, aws_creds) -> tuple[bytes, dict]:
    """
    Download processed audio file for a completed job.
    
    Business logic:
    1. Check job exists and belongs to user
    2. Check job status is 'done'
    3. Download audio file from S3
    4. Return audio bytes and metadata
    
    Args:
        job_id: Job ID
        user_id: User ID for permission check
        db: Database session
        s3_client: Boto3 S3 client
        aws_creds: AWS credentials dict
    
    Returns:
        Tuple of (audio_bytes, audio_metadata)
    
    Raises:
        PermissionError: Job not found or access denied
        ValueError: Job not completed
        FileNotFoundError: File not found in S3
        RuntimeError: S3 download failed
    """
    from app.repositories import job_repository
    from botocore.exceptions import ClientError
    
    logger.info(f"Getting audio file for job {job_id}, user {user_id}")
    
    # 1. Check job status and get audio metadata
    result = job_repository.get_job_status_with_audio_metadata(db, job_id, user_id)
    
    if not result:
        raise PermissionError("Job not found or access denied")
    
    status, audio_metadata = result
    
    if status != 'done':
        raise ValueError(f"Job not completed. Current status: {status}")
    
    # 2. Download from S3
    s3_key = f"processed_audio/{job_id}.mp3"
    
    try:
        response = s3_client.get_object(
            Bucket=aws_creds["s3_bucket"],
            Key=s3_key
        )
        return response['Body'].read(), audio_metadata
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.error(f"Audio file not found in S3: {s3_key}")
            raise FileNotFoundError("Audio file not found in S3")
        else:
            logger.error(f"S3 download failed: {str(e)}")
            raise RuntimeError(f"S3 download failed: {str(e)}")

def get_pdf_file(job_id: str, user_id: str, db, s3_client, aws_creds) -> bytes:
    """
    Download PDF file for a completed job.
    """
    
    from app.repositories import job_repository
    from botocore.exceptions import ClientError
    
    logger.info(f"Getting PDF file for job {job_id}, user {user_id}")
    
    # 1. Check job status
    status = job_repository.get_job_status_for_user(db, job_id, user_id)
    
    if not status:
        raise PermissionError("Job not found or access denied")
    
    if status != 'done':
        raise ValueError(f"Job not completed. Current status: {status}")
    
    # 2. Download from S3
    s3_key = f"pdf/{job_id}.pdf"
    
    try:
        response = s3_client.get_object(
            Bucket=aws_creds["s3_bucket"],
            Key=s3_key
        )
        return response['Body'].read()
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.error(f"PDF file not found in S3: {s3_key}")
            raise FileNotFoundError("PDF file not found in S3")
        else:
            logger.error(f"S3 download failed: {str(e)}")
            raise RuntimeError(f"S3 download failed: {str(e)}")