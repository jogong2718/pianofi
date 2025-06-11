from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
from app.schemas.createJob import CreateJobPayload
from app.schemas.createJob import CreateJobResponse
from app.schemas.user import User
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
import os
from packages.pianofi_config.config import Config
import time
import redis
import json
import logging
from app.auth import get_current_user

router = APIRouter()

DATABASE_URL = Config.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

r = redis.from_url(Config.REDIS_URL, decode_responses=True)

@router.post("/createJob", response_model=CreateJobResponse)
async def create_job(payload: CreateJobPayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Create a job with a unique jobId and fileKey.
    This endpoint is used to initiate a job for processing an audio file.
    """
    try:
        authenticated_user_id = current_user.id

        if not payload.jobId or not payload.fileKey:
            raise HTTPException(status_code=400, detail="jobId and fileKey are required")
        
        sql = text("""
            SELECT EXISTS(SELECT 1 FROM jobs 
                         WHERE job_id = :jobId AND user_id = :userId)
        """)

        result = db.execute(sql, {
            "jobId": payload.jobId, 
            "userId": authenticated_user_id  # Use server-side user ID
        }).fetchone()
        
        if not result[0]:
            raise HTTPException(status_code=404, detail="Job not found or access denied")
        
        update_sql = text("""
            UPDATE jobs
            SET status = 'queued', queued_at = NOW()
            WHERE job_id = :jobId AND file_key = :fileKey
        """)

        update_result = db.execute(update_sql, {"jobId": payload.jobId, "fileKey": payload.fileKey})

        if update_result.rowcount == 0:
            raise HTTPException(status_code=400, detail="Job not found or fileKey mismatch")
        
        db.commit()
        # Here you would typically add the job to a queue for processing

        # Enqueue the job in redis
        job_data = {
            "jobId": payload.jobId,
            "fileKey": payload.fileKey,
            "userId": authenticated_user_id,
            "createdAt": time.time()
        }

        r.lpush("job_queue", json.dumps(job_data))  # Push job data to Redis list
        # Log the job creation
        logging.info(f"Job created: {payload.jobId}, fileKey: {payload.fileKey}, userId: {authenticated_user_id}")

        # Simulate saving the job (e.g., to a database)
        # In a real application, you would save this to your database here
        # WORK ON THIS WE NEED TO DECIDE OUR DB AND I NEED TO LEARN REDIS LMAO

        return CreateJobResponse(success=True)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
