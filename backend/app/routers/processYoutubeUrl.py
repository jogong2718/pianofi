import uuid
import os
import logging
import time
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
import redis
import yt_dlp

from app.config_loader import Config
from app.schemas.processYoutubeUrl import ProcessYoutubeUrlPayload, ProcessYoutubeUrlResponse
from app.schemas.user import User
from app.auth import get_current_user
from app.database import get_db

router = APIRouter()

# get configuration
aws_creds = Config.AWS_CREDENTIALS
local = Config.USE_LOCAL_STORAGE == "true"
r = redis.from_url(Config.REDIS_URL, decode_responses=True)

if local:
    UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
    UPLOAD_DIR.mkdir(exist_ok=True)

# S3 client setup if not local
if not local:
    import boto3
    s3_client = boto3.client(
        "s3",
        region_name=aws_creds["aws_region"],
    )

@router.post("/processYoutubeUrl", response_model=ProcessYoutubeUrlResponse)
async def process_youtube_url(
    payload: ProcessYoutubeUrlPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # download audio from YouTube URL, save it, create a job, and queue it for processing.

    logging.info(f"Received YouTube URL process request: {payload.youtube_url}")

    try:
        authenticated_user_id = current_user.id
        logging.info(f"User authenticated: {authenticated_user_id}")

        # validate YouTube URL
        if not is_valid_youtube_url(payload.youtube_url):
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")

        # generate job ID and file key
        job_id = str(uuid.uuid4())
        file_ext = ".mp3"
        file_key = f"mp3/{job_id}{file_ext}"

        # download audio from YouTube
        try:
            if local:
                download_path = UPLOAD_DIR / "mp3"
                download_path.mkdir(exist_ok=True, parents=True)
                # don't include extension in outtmpl - yt-dlp will add it
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
                    info = ydl.extract_info(payload.youtube_url, download=True)
                    video_title = info.get('title', 'Unknown')
                    duration = info.get('duration', 0)

                # yt-dlp adds .mp3 extension automatically
                output_file = download_path / f"{job_id}.mp3"
                file_size = output_file.stat().st_size

            else:
                # download to temp location then upload to S3
                import tempfile
                with tempfile.TemporaryDirectory() as temp_dir:
                    # don't include extension in outtmpl - yt-dlp will add it
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
                        info = ydl.extract_info(payload.youtube_url, download=True)
                        video_title = info.get('title', 'Unknown')
                        duration = info.get('duration', 0)

                    # yt-dlp adds .mp3 extension automatically
                    temp_output = Path(temp_dir) / f"{job_id}.mp3"

                    # upload to S3
                    file_size = temp_output.stat().st_size
                    with open(temp_output, 'rb') as f:
                        s3_client.put_object(
                            Bucket=aws_creds["s3_bucket"],
                            Key=file_key,
                            Body=f,
                            ContentType="audio/mpeg"
                        )

        except Exception as e:
            logging.error(f"Failed to download YouTube video: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to download audio from YouTube: {str(e)}")

        # create job in database
        sql = text("""
            INSERT INTO jobs (job_id, file_key, status, user_id, file_name, file_size, file_duration, model, level, queued_at)
            VALUES (:job_id, :file_key, 'queued', :user_id, :file_name, :file_size, :file_duration, :model, :level, NOW())
        """)

        db.execute(sql, {
            "job_id": job_id,
            "file_key": file_key,
            "user_id": authenticated_user_id,
            "file_name": f"{video_title}.mp3",
            "file_size": file_size,
            "file_duration": duration,
            "model": payload.model,
            "level": payload.level
        })

        db.commit()

        # queue the job in Redis
        job_data = {
            "jobId": job_id,
            "fileKey": file_key,
            "userId": authenticated_user_id,
            "createdAt": time.time(),
            "model": payload.model,
            "level": payload.level
        }

        if payload.model == "picogen":
            r.lpush("picogen_job_queue", json.dumps(job_data))
        elif payload.model == "amt":
            r.lpush("amt_job_queue", json.dumps(job_data))

        logging.info(f"YouTube job created: {job_id}, model: {payload.model}, video: {video_title}")

        return ProcessYoutubeUrlResponse(
            jobId=job_id,
            fileKey=file_key,
            success=True
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Error processing YouTube URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def is_valid_youtube_url(url: str) -> bool:
    # validate if the URL is a valid YouTube URL
    youtube_domains = ['youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com']
    return any(domain in url for domain in youtube_domains)
