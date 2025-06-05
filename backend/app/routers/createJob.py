from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
from app.schemas.createJob import CreateJobPayload
from app.schemas.createJob import CreateJobResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
import os
from app.config import Config
import time

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

@router.post("/createJob", response_model=CreateJobResponse)
async def create_job(payload: CreateJobPayload, db: Session = Depends(get_db)):
    """
    Create a job with a unique jobId and fileKey.
    This endpoint is used to initiate a job for processing an audio file.
    """
    try:
        if not payload.jobId or not payload.fileKey:
            raise HTTPException(status_code=400, detail="jobId and fileKey are required")
        
        sql = text("""
            SELECT EXISTS(SELECT 1 FROM jobs WHERE job_id = :jobId)
        """)

        result = db.execute(sql, {"jobId": payload.jobId}).fetchone()
        if not result[0]:
            raise HTTPException(status_code=404, detail="Job not found")
        
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
        
        



        # Simulate saving the job (e.g., to a database)
        # In a real application, you would save this to your database here
        # WORK ON THIS WE NEED TO DECIDE OUR DB AND I NEED TO LEARN REDIS LMAO

        return CreateJobResponse(success=True)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
