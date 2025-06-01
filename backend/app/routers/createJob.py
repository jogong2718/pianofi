from fastapi import APIRouter, HTTPException
from pathlib import Path
from app.schemas.createJob import CreateJobPayload
from app.schemas.createJob import CreateJobResponse

router = APIRouter()

@router.post("/createJob", response_model=CreateJobResponse)
async def create_job(payload: CreateJobPayload):
    """
    Create a job with a unique jobId and fileKey.
    This endpoint is used to initiate a job for processing an audio file.
    """
    try:
        if not payload.jobId or not payload.fileKey:
            raise HTTPException(status_code=400, detail="jobId and fileKey are required")

        # Simulate saving the job (e.g., to a database)
        # In a real application, you would save this to your database here
        # WORK ON THIS WE NEED TO DECIDE OUR DB AND I NEED TO LEARN REDIS LMAO

        return CreateJobResponse(success=True)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

