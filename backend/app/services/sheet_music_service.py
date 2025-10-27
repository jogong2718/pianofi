"""
Sheet Music Service - Handles sheet music generation and management.

Functions for generating, retrieving, and managing sheet music.
Serves routers: createSheetMusic
"""

from typing import Dict, Any, Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


def create_sheet_music(
    user_id: UUID,
    job_id: UUID,
    format: str,
    options: Optional[Dict[str, Any]],
    sheet_music_repository,
    job_repository,
    storage_service_funcs: Dict[str, callable],
    task_queue
) -> Dict[str, Any]:
    """
    Create sheet music from a completed transcription job.
    
    Business logic:
    1. Verify job exists and is completed
    2. Verify user owns the job
    3. Validate format and options
    4. Enqueue sheet music generation task
    5. Return sheet music record
    
    Args:
        user_id: UUID of the requesting user
        job_id: UUID of the completed transcription job
        format: Output format (pdf, musicxml, midi)
        options: Optional customization (clef, layout, transpose, etc.)
        sheet_music_repository: Repository for sheet music records
        job_repository: Repository for job data
        storage_service_funcs: Dict of storage service functions
        task_queue: Queue for background rendering tasks
    
    Returns:
        Dict containing sheet music details (id, status, job_id, etc.)
    
    Raises:
        NotFoundError: Job not found
        UnauthorizedError: User doesn't own this job
        ValidationError: Invalid format or options
        JobNotCompleteError: Job not yet completed
    """
    logger.info(f"Creating sheet music for user {user_id}, job {job_id}, format {format}")
    
    # TODO: Implement
    # 1. Verify job: job = job_repository.find_by_id(job_id)
    # 2. Check ownership: if job.user_id != user_id: raise UnauthorizedError()
    # 3. Check status: if job.status != "completed": raise JobNotCompleteError()
    # 4. Create record: sheet_music = sheet_music_repository.save(SheetMusic(...))
    # 5. Enqueue generation: task_queue.enqueue_sheet_music_generation(sheet_music.id, format, options)
    # 6. Return details
    
    raise NotImplementedError("Sheet music creation logic to be moved from router")


def get_sheet_music(
    sheet_music_id: UUID,
    user_id: UUID,
    sheet_music_repository,
    job_repository,
    storage_service_funcs: Dict[str, callable]
) -> Dict[str, Any]:
    """
    Get sheet music details by ID.
    
    Args:
        sheet_music_id: UUID of the sheet music
        user_id: UUID of the requesting user (for authorization)
        sheet_music_repository: Repository for sheet music data
        job_repository: Repository for job data
        storage_service_funcs: Dict of storage service functions
    
    Returns:
        Sheet music details including download URL
    
    Raises:
        NotFoundError: Sheet music not found
        UnauthorizedError: User doesn't have access
    """
    logger.info(f"Fetching sheet music {sheet_music_id} for user {user_id}")
    
    # TODO: Implement
    # 1. Get sheet music: sm = sheet_music_repository.find_by_id(sheet_music_id)
    # 2. Verify ownership via job_id
    # 3. Generate download URL if ready: sm.download_url = storage_service_funcs["generate_download_url"](sm.file_key, ...)
    # 4. Return details
    
    raise NotImplementedError()


def list_sheet_music_for_job(
    job_id: UUID,
    user_id: UUID,
    sheet_music_repository,
    job_repository
) -> list:
    """
    List all sheet music generated for a specific job.
    
    Args:
        job_id: UUID of the job
        user_id: UUID of the requesting user (for authorization)
        sheet_music_repository: Repository for sheet music data
        job_repository: Repository for job data
    
    Returns:
        List of sheet music records
    """
    logger.info(f"Listing sheet music for job {job_id}, user {user_id}")
    
    # TODO: Implement
    # 1. Verify ownership
    # 2. Get sheet music: sheet_music_repository.find_by_job_id(job_id)
    
    raise NotImplementedError()


def update_sheet_music_status(
    sheet_music_id: UUID,
    status: str,
    file_key: Optional[str],
    error_message: Optional[str],
    sheet_music_repository
) -> None:
    """
    Update sheet music generation status (called by background workers).
    
    Args:
        sheet_music_id: UUID of the sheet music
        status: New status (processing, completed, failed)
        file_key: S3 key of the generated file (if completed)
        error_message: Error message (if failed)
        sheet_music_repository: Repository for sheet music data
    """
    logger.info(f"Updating sheet music {sheet_music_id} status to {status}")
    
    # TODO: Implement
    # updates = {"status": status}
    # if file_key:
    #     updates["file_key"] = file_key
    # if error_message:
    #     updates["error_message"] = error_message
    # sheet_music_repository.update(sheet_music_id, updates)
    
    raise NotImplementedError()


def delete_sheet_music(
    sheet_music_id: UUID,
    user_id: UUID,
    sheet_music_repository,
    job_repository,
    storage_service_funcs: Dict[str, callable]
) -> bool:
    """
    Delete sheet music and its associated file.
    
    Args:
        sheet_music_id: UUID of the sheet music
        user_id: UUID of the requesting user (for authorization)
        sheet_music_repository: Repository for sheet music data
        job_repository: Repository for job data
        storage_service_funcs: Dict of storage service functions
    
    Returns:
        True if deleted successfully
    """
    logger.info(f"Deleting sheet music {sheet_music_id} for user {user_id}")
    
    # TODO: Implement
    # 1. Get sheet music and verify ownership
    # 2. Delete file from S3: storage_service_funcs["delete_file"](sm.file_key, user_id, ...)
    # 3. Delete DB record: sheet_music_repository.delete(sheet_music_id)
    
    raise NotImplementedError()


# ========================================
# Functions moved from createSheetMusic.py router
# ========================================

def convert_midi_to_xml(midi_file_path: str, output_path: str) -> str:
    """
    Convert MIDI file to MusicXML format.
    
    Args:
        midi_file_path: Path to input MIDI file
        output_path: Base path for output file
    
    Returns:
        Path to generated MusicXML file
    
    Raises:
        RuntimeError: If conversion fails
    """
    try:
        from music21 import converter, key
        
        score = converter.parse(midi_file_path)
        
        if not score.analyze('key'):
            score.insert(0, key.KeySignature(0))
        
        output_file = f"{output_path}.musicxml"
        score.write('musicxml', fp=output_file)
        return output_file
        
    except Exception as e:
        logger.error(f"XML conversion failed: {str(e)}")
        raise RuntimeError(f"XML conversion failed: {str(e)}")


def convert_midi_to_visual(midi_file_path: str, output_path: str, format: str, title: str = None, composer: str = None) -> str:
    """
    Convert MIDI file to visual format (PDF/PNG/SVG) using Lilypond.
    
    Args:
        midi_file_path: Path to input MIDI file
        output_path: Base path for output file
        format: Output format (pdf, png, svg)
        title: Optional title for the score
        composer: Optional composer name
    
    Returns:
        Path to generated visual file
    
    Raises:
        RuntimeError: If conversion fails
    """
    import subprocess
    import os
    
    try:
        from music21 import converter, meter, key, tempo
        
        score = converter.parse(midi_file_path)
        
        if title:
            score.insert(0, meter.MetronomeMark(title))
        if composer:
            score.insert(0, tempo.TempoIndication(composer))
        
        if not score.analyze('key'):
            score.insert(0, key.KeySignature(0))
        
        output_file = f"{output_path}.{format.lower()}"
        lily_file = f"{output_path}.ly"
        
        score.write('lily', fp=lily_file)
        
        subprocess.run([
            "lilypond", 
            f"--{format.lower()}", 
            "-o", output_path.replace(f".{format.lower()}", ""),
            lily_file
        ], check=True)
        
        if os.path.exists(lily_file):
            os.remove(lily_file)
        
        return output_file
        
    except Exception as e:
        logger.error(f"Visual conversion failed: {str(e)}")
        raise RuntimeError(f"Visual conversion failed: {str(e)}")


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
