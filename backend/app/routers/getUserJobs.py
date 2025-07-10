from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.auth import get_current_user
from app.schemas.user import User
from typing import List
from app.config_loader import Config 
from app.schemas.getUserJobs import UserJobResponse  # Assuming this schema exists for the response model
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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

@router.get("/getUserJobs", response_model=List[UserJobResponse])
async def get_user_jobs(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get all jobs for the current user"""
    try:
        print(f"Fetching jobs for user: {current_user.id}")

        sql = text("""
            SELECT job_id, status, created_at, result_key, file_name, file_size, file_duration
            FROM jobs 
            WHERE user_id = :user_id 
            AND status != 'deleted'
            ORDER BY created_at DESC
        """)
        
        result = db.execute(sql, {"user_id": current_user.id}).fetchall()
        
        jobs = []
        for row in result:
            try:
                created_at_str = row[2].isoformat() if row[2] else ""
                jobs.append(UserJobResponse(
                    job_id=str(row[0]),
                    status=row[1],
                    created_at=created_at_str,
                    result_key=row[3] if row[3] is not None else "",
                    file_name=row[4] if row[4] is not None else "Unknown",
                    file_size=row[5] if row[5] is not None else 0,
                    file_duration=row[6] if row[6] is not None else 0
                ))
            except Exception as row_error:
                print(f"Error processing row {row}: {str(row_error)}")
        
        return jobs
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in getUserJobs: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")