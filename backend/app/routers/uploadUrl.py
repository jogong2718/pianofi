# app/routers/upload.py

from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
from sqlalchemy.orm import Session
import boto3

# app/schemas/uploadUrl.py
from app.config_loader import Config 
from app.schemas.uploadUrl import UploadUrlResponse
from app.schemas.uploadUrl import CreateUrlPayload
from app.schemas.user import User
from app.auth import get_current_user
from app.database import get_db
from app.services import storage_service
from app.repositories import job_repository

router = APIRouter()

# 2) Grab S3 settings from environment
aws_creds = Config.AWS_CREDENTIALS
local = Config.USE_LOCAL_STORAGE == "true"

if local:
    UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
    UPLOAD_DIR.mkdir(exist_ok=True)

# 3) Create a boto3 S3 client
if not local:
    s3_client = boto3.client(
        "s3",
        region_name=aws_creds["aws_region"],
    )

@router.post("/uploadUrl", response_model=UploadUrlResponse)
def create_upload_url(
    payload: CreateUrlPayload, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Generate a presigned PUT URL for S3, plus a jobId and fileKey.
    The client will PUT its file directly to S3 at this URL.
    """
    try:
        # 1. Generate upload URL using storage service
        result = storage_service.generate_upload_url(
            user_id=current_user.id,
            filename=payload.file_name,
            file_size=payload.file_size,
            content_type=payload.content_type,
            s3_client=s3_client if not local else None,
            aws_creds=aws_creds,
            use_local=local,
            local_upload_dir=str(UPLOAD_DIR) if local else None
        )
        print("IT WORKS")
        
        # 2. Create job record in database using repository
        job_data = {
            "job_id": result["job_id"],
            "file_key": result["file_key"],
            "status": "initialized",
            "user_id": current_user.id,
            "file_name": payload.file_name,
            "file_size": payload.file_size,
            "file_duration": None
        }
        
        job_repository.save(db, job_data)
        db.commit()
        
        # 3. Return response
        return UploadUrlResponse(
            uploadUrl=result["upload_url"],
            jobId=result["job_id"],
            fileKey=result["file_key"],
        )
    
    except ValueError as e:
        # Validation errors from service
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        # Any other errors
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
