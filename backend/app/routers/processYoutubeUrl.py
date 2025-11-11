import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import redis

from app.config_loader import Config
from app.schemas.processYoutubeUrl import ProcessYoutubeUrlPayload, ProcessYoutubeUrlResponse
from app.schemas.user import User
from app.auth import get_current_user
from app.database import get_db
from app.services import youtube_service

router = APIRouter()

# Get configuration
aws_creds = Config.AWS_CREDENTIALS
local = Config.USE_LOCAL_STORAGE == "true"
r = redis.from_url(Config.REDIS_URL, decode_responses=True)

if local:
    UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
    UPLOAD_DIR.mkdir(exist_ok=True)
    s3_client = None
else:
    # S3 client setup if not local
    import boto3
    s3_client = boto3.client(
        "s3",
        region_name=aws_creds["aws_region"],
    )
    UPLOAD_DIR = None

@router.post("/processYoutubeUrl", response_model=ProcessYoutubeUrlResponse)
async def process_youtube_url(
    payload: ProcessYoutubeUrlPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process a YouTube URL to download audio and create a transcription job.

    This endpoint handles:
    1. Rate limiting (100 downloads per hour globally)
    2. YouTube URL validation
    3. Audio download via yt-dlp
    4. Job creation in database
    5. Queueing for processing in Redis
    """
    logging.info(f"Received YouTube URL process request: {payload.youtube_url}")

    try:
        # Call service layer to handle business logic
        result = youtube_service.process_youtube_url(
            youtube_url=payload.youtube_url,
            model=payload.model,
            level=payload.level,
            user_id=current_user.id,
            db=db,
            redis_client=r,
            use_local=local,
            local_upload_dir=UPLOAD_DIR,
            s3_client=s3_client,
            aws_creds=aws_creds
        )

        logging.info(
            f"YouTube job processed successfully: {result['job_id']}, "
            f"model: {payload.model}, user: {current_user.id}"
        )

        return ProcessYoutubeUrlResponse(
            jobId=result["job_id"],
            fileKey=result["file_key"],
            success=result["success"]
        )

    except HTTPException:
        # HTTPExceptions from service layer are already properly formatted
        db.rollback()
        raise

    except Exception as e:
        # Unexpected errors
        db.rollback()
        logging.error(f"Error processing YouTube URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
