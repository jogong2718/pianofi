from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.auth import get_current_user
from app.schemas.user import User
from typing import List
from app.config_loader import Config 
from app.schemas.getUserJobs import UserJobResponse
from app.database import get_db

router = APIRouter()

@router.get("/getUserJobs", response_model=List[UserJobResponse])
async def get_user_jobs(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get all jobs for the current user"""
    try:
        print(f"Fetching jobs for user: {current_user.id}")

        # Use parameterized query to prevent SQL injection
        sql = text("""
            SELECT 
                job_id,
                file_name,
                file_size,
                status,
                created_at,
                queued_at,
                started_at,
                finished_at,
                model,
                level
            FROM jobs 
            WHERE user_id = :user_id
            AND status != 'deleted' 
            ORDER BY created_at DESC
        """)
        
        result = db.execute(sql, {"user_id": current_user.id})
        jobs = result.fetchall()
        
        # Convert to list of dictionaries
        jobs_list = []
        for job in jobs:
            job_dict = {
                "job_id": str(job.job_id),
                "file_name": job.file_name,
                "file_size": job.file_size,
                "status": job.status,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "queued_at": job.queued_at.isoformat() if job.queued_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "finished_at": job.finished_at.isoformat() if job.finished_at else None,
                "model": job.model,
                "level": job.level
            }
            jobs_list.append(job_dict)
        
        print(f"Found {len(jobs_list)} jobs for user {current_user.id}")
        return jobs_list
        
    except Exception as e:
        print(f"Error fetching jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch jobs: {str(e)}")