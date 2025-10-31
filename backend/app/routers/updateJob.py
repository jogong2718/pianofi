from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.schemas.user import User
from app.schemas.updateJob import UpdateJobRequest, UpdateJobResponse
from app.database import get_db
from app.services import job_service
from app.repositories import job_repository

router = APIRouter()

@router.put("/updateJob", response_model=UpdateJobResponse)
async def update_job(
    job_data: UpdateJobRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Call service to handle the update logic
        result = job_service.update_job(
            job_id=job_data.job_id,
            user_id=current_user.id,
            file_name=job_data.file_name,
            db=db,
            job_repository=job_repository
        )
        
        return UpdateJobResponse(**result)
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
