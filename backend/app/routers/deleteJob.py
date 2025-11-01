from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.schemas.user import User
from app.schemas.deleteJob import deleteJobResponse
from app.database import get_db
from app.services import job_service

router = APIRouter()

@router.delete("/deleteJob/{job_id}", tags=["jobs"], response_model=deleteJobResponse)
def delete_job(
    job_id: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete a job by setting status to 'deleted'"""
    try:
        # Call service layer
        result = job_service.delete_job(
            job_id=job_id,
            user_id=current_user.id,
            db=db
        )
        
        db.commit()
        
        return deleteJobResponse(**result)
        
    except PermissionError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting job: {str(e)}")