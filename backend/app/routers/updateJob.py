from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.auth import get_current_user
from app.schemas.user import User
from app.schemas.updateJob import UpdateJobRequest, UpdateJobResponse
from app.database import get_db

router = APIRouter()

@router.put("/updateJob", response_model=UpdateJobResponse)
async def update_job(
    job_data: UpdateJobRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        update_sql = text("""
            UPDATE jobs 
            SET file_name = :file_name
            WHERE job_id = :job_id AND user_id = :user_id
        """)
        
        result = db.execute(update_sql, {
            "file_name": job_data.file_name,
            "job_id": job_data.job_id,
            "user_id": current_user.id
        })
        
        if result.rowcount == 0:
            db.rollback()
            raise HTTPException(status_code=404, detail="Job not found or access denied")
        
        db.commit()
        
        return UpdateJobResponse(
            success=True,
            message="Job updated successfully"
        )
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
