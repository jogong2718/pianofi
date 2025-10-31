"""
YouTube Service - Handles YouTube URL processing and audio download.

Functions for downloading audio from YouTube URLs, rate limiting, and job creation.
Serves router: processYoutubeUrl
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging
import time
import json
import uuid
import tempfile
from fastapi import HTTPException
import yt_dlp

logger = logging.getLogger(__name__)


def is_valid_youtube_url(url: str) -> bool:
    """
    Validate if the URL is a valid YouTube URL.

    Args:
        url: URL string to validate

    Returns:
        True if valid YouTube URL, False otherwise
    """
    youtube_domains = ['youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com']
    return any(domain in url for domain in youtube_domains)


def check_rate_limit(redis_client) -> Optional[int]:
    """
    Check YouTube download rate limit (100 downloads per hour globally).

    Args:
        redis_client: Redis client for rate limiting

    Returns:
        None if allowed, wait_time in seconds if rate limited
    """
    one_hour_ago = time.time() - 3600  # 3600 seconds in an hour

    # Remove entries older than one hour
    redis_client.zremrangebyscore("youtube_downloads", 0, one_hour_ago)

    # Count recent downloads
    download_count = redis_client.zcard("youtube_downloads")

    if download_count >= 100:
        # Get oldest entry to inform user when they can try again
        oldest_downloads = redis_client.zrange("youtube_downloads", 0, 0, withscores=True)
        if oldest_downloads:
            oldest_timestamp = oldest_downloads[0][1]  # timestamp of the oldest entry
            wait_time = int(oldest_timestamp + 3600 - time.time())  # time until the oldest entry is one hour old
            if wait_time > 0:
                logger.warning(f"Rate limit exceeded. Must wait {wait_time} seconds.")
                return wait_time

    return None


def download_youtube_audio(
    youtube_url: str,
    job_id: str,
    use_local: bool = False,
    local_upload_dir: Optional[Path] = None,
    s3_client=None,
    aws_creds: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Download audio from YouTube URL and upload to storage (S3 or local).

    Args:
        youtube_url: YouTube video URL
        job_id: Generated job ID
        use_local: Whether to use local storage
        local_upload_dir: Local directory for uploads (if use_local=True)
        s3_client: S3 client for production uploads
        aws_creds: AWS credentials dict with s3_bucket

    Returns:
        Dict containing:
            - file_key: Storage key where file is stored
            - file_size: Size of downloaded file in bytes
            - video_title: Title of the YouTube video
            - duration: Duration of video in seconds

    Raises:
        Exception: Download or upload failed
    """
    file_ext = ".mp3"
    file_key = f"mp3/{job_id}{file_ext}"

    try:
        if use_local:
            download_path = local_upload_dir / "mp3"
            download_path.mkdir(exist_ok=True, parents=True)
            # Don't include extension in outtmpl - yt-dlp will add it
            output_file_base = download_path / job_id

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(output_file_base),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,  # Only download single video, not playlist
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                video_title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)

            # yt-dlp adds .mp3 extension automatically
            output_file = download_path / f"{job_id}.mp3"
            file_size = output_file.stat().st_size

        else:
            # Download to temp location then upload to S3
            with tempfile.TemporaryDirectory() as temp_dir:
                # Don't include extension in outtmpl - yt-dlp will add it
                temp_output_base = Path(temp_dir) / job_id

                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': str(temp_output_base),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True,  # Only download single video, not playlist
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(youtube_url, download=True)
                    video_title = info.get('title', 'Unknown')
                    duration = info.get('duration', 0)

                # yt-dlp adds .mp3 extension automatically
                temp_output = Path(temp_dir) / f"{job_id}.mp3"

                # Upload to S3
                file_size = temp_output.stat().st_size
                with open(temp_output, 'rb') as f:
                    s3_client.put_object(
                        Bucket=aws_creds["s3_bucket"],
                        Key=file_key,
                        Body=f,
                        ContentType="audio/mpeg"
                    )

        logger.info(f"Successfully downloaded YouTube audio: {video_title} ({file_size} bytes)")

        return {
            "file_key": file_key,
            "file_size": file_size,
            "video_title": video_title,
            "duration": duration
        }

    except Exception as e:
        logger.error(f"Failed to download YouTube video: {str(e)}")
        raise Exception(f"Failed to download audio from YouTube: {str(e)}")


def process_youtube_url(
    youtube_url: str,
    model: str,
    level: int,
    user_id: str,
    db,
    redis_client,
    use_local: bool = False,
    local_upload_dir: Optional[Path] = None,
    s3_client=None,
    aws_creds: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Process YouTube URL: download audio, create job, and queue for processing.

    Business logic:
    1. Check rate limit (100 downloads per hour globally)
    2. Validate YouTube URL
    3. Generate job ID
    4. Download audio from YouTube
    5. Create job in database
    6. Add to Redis queue
    7. Track download in rate limiting

    Args:
        youtube_url: YouTube video URL
        model: Model to use ('amt' or 'picogen')
        level: Processing level (1-3)
        user_id: ID of the user making the request
        db: Database session
        redis_client: Redis client for queue and rate limiting
        use_local: Whether to use local storage
        local_upload_dir: Local directory for uploads (if use_local=True)
        s3_client: S3 client for production uploads
        aws_creds: AWS credentials dict

    Returns:
        Dict containing:
            - job_id: Generated job ID
            - file_key: Storage key for the downloaded file
            - success: True

    Raises:
        HTTPException: Rate limited, invalid URL, or processing failed
    """
    logger.info(f"Processing YouTube URL for user {user_id}: {youtube_url}")

    # 1. Check rate limit
    wait_time = check_rate_limit(redis_client)
    if wait_time is not None:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Please try again in {wait_time} seconds."
        )

    # 2. Validate YouTube URL
    if not is_valid_youtube_url(youtube_url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    # 3. Generate job ID
    job_id = str(uuid.uuid4())

    # 4. Download audio from YouTube
    try:
        download_result = download_youtube_audio(
            youtube_url=youtube_url,
            job_id=job_id,
            use_local=use_local,
            local_upload_dir=local_upload_dir,
            s3_client=s3_client,
            aws_creds=aws_creds
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 5. Create job in database
    from sqlalchemy import text

    sql = text("""
        INSERT INTO jobs (job_id, file_key, status, user_id, file_name, file_size, file_duration, model, level, queued_at)
        VALUES (:job_id, :file_key, 'queued', :user_id, :file_name, :file_size, :file_duration, :model, :level, NOW())
    """)

    db.execute(sql, {
        "job_id": job_id,
        "file_key": download_result["file_key"],
        "user_id": user_id,
        "file_name": f"{download_result['video_title']}.mp3",
        "file_size": download_result["file_size"],
        "file_duration": download_result["duration"],
        "model": model,
        "level": level
    })

    db.commit()

    # 6. Queue the job in Redis
    job_data = {
        "jobId": job_id,
        "fileKey": download_result["file_key"],
        "userId": user_id,
        "createdAt": time.time(),
        "model": model,
        "level": level
    }

    # Determine queue based on model and environment
    from app.services.job_service import get_queue_name
    from app.config_loader import Config

    try:
        queue_name = get_queue_name(model, Config.ENVIRONMENT)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    redis_client.lpush(queue_name, json.dumps(job_data))

    # 7. Add to rate limiting sorted set
    redis_client.zadd("youtube_downloads", {job_id: time.time()})

    logger.info(
        f"YouTube job created and queued: {job_id}, model: {model}, "
        f"video: {download_result['video_title']}"
    )

    return {
        "job_id": job_id,
        "file_key": download_result["file_key"],
        "success": True
    }
