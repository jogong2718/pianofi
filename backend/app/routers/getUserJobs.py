from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.schemas.user import User
from typing import List
from app.schemas.getUserJobs import UserJobResponse
from app.database import get_db
from app.services import job_service
from app.repositories import job_repository

router = APIRouter()

@router.get("/getUserJobs", response_model=List[UserJobResponse])
async def get_user_jobs(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get all jobs for the current user"""
    try:
        print(f"Fetching jobs for user: {current_user.id}")
        
        # Call service to handle the logic
        jobs_list = job_service.get_user_jobs(
            user_id=current_user.id,
            db=db,
            job_repository=job_repository
        )
        
        print(f"Found {len(jobs_list)} jobs for user {current_user.id}")
        return jobs_list
        
    except Exception as e:
        print(f"Error fetching jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch jobs: {str(e)}")