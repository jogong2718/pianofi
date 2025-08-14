from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.auth import get_current_user
from app.schemas.user import User
from app.config_loader import Config
from app.schemas.deleteJob import deleteJobResponse
from app.database import get_db

router = APIRouter()

@router.delete("/deleteJob/{job_id}", tags=["jobs"], response_model=deleteJobResponse)
def delete_job(
    job_id: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete a job by setting status to 'deleted'"""
    try:
        # Update job status to 'deleted'
        result = db.execute(
            text("""
                UPDATE jobs 
                SET status = 'deleted'
                WHERE job_id = :job_id AND user_id = :user_id
                RETURNING job_id
            """),
            {"job_id": job_id, "user_id": current_user.id}
        )
        
        deleted_job = result.fetchone()
        if not deleted_job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        db.commit()
        return deleteJobResponse(
            message="Job successfully deleted",
            jobId=str(deleted_job[0])
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting job: {str(e)}")