from fastapi import APIRouter, HTTPException, Depends
from app.schemas.createJob import CreateJobPayload
from app.schemas.createJob import CreateJobResponse
from app.schemas.user import User
from sqlalchemy.orm import Session
from app.config_loader import Config 
import redis
import logging
from app.auth import get_current_user
from app.database import get_db
from app.services import job_service

router = APIRouter()

# Initialize Redis client for queue operations
r = redis.from_url(Config.REDIS_URL, decode_responses=True)

@router.post("/createJob", response_model=CreateJobResponse)
async def create_job(
    payload: CreateJobPayload, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Queue an existing job for processing.
    
    This endpoint is called after a file has been uploaded to start the transcription process.
    It validates the job, updates its status to 'queued', and adds it to the Redis queue
    for processing by background workers.
    """
    try:
        # Call service layer to handle business logic
        result = job_service.queue_job(
            job_id=payload.jobId,
            file_key=payload.fileKey,
            user_id=current_user.id,
            model=payload.model,
            level=payload.level,
            db=db,
            redis_client=r
        )
        
        logging.info(
            f"Job queued successfully: {payload.jobId} in {payload.model}, "
            f"fileKey: {payload.fileKey}, userId: {current_user.id}"
        )
        
        return CreateJobResponse(success=result["success"])
    
    except ValueError as e:
        # Validation errors (missing fields, unknown model)
        raise HTTPException(status_code=400, detail=str(e))
    
    except PermissionError as e:
        # Permission errors (job not found or access denied)
        raise HTTPException(status_code=404, detail=str(e))
    
    except RuntimeError as e:
        # Update failures (fileKey mismatch)
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        # Unexpected errors
        db.rollback()
        logging.error(f"Error queueing job {payload.jobId}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
