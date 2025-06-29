import uuid
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from typing import List
import os

# app/schemas/uploadUrl.py
from app.config_loader import Config 
from app.schemas.getDownload import getDownloadResponse
from app.schemas.user import User
from app.auth import get_current_user

router = APIRouter()

DATABASE_URL = Config.DATABASE_URL
aws_creds = Config.AWS_CREDENTIALS
local = Config.ENVIRONMENT == "development"

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

s3_client = None
if not local:
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_creds["aws_access_key_id"],
        aws_secret_access_key=aws_creds["aws_secret_access_key"],
        region_name=aws_creds["aws_region"],
    )

@router.get("/getDownload/{job_id}", response_model=getDownloadResponse, tags=["jobs"])
def get_user_jobs(job_id: str, db: Session = Depends(get_db)):
    """
    Fetch a job by its unique jobId.
    This endpoint retrieves the downloadlink of a job based on the provided jobId.
    """
    try:
        if local:
            # Use absolute URL with your backend base URL
            backend_base = Config.BACKEND_BASE_URL or "http://localhost:8000"
            download_url = f"{backend_base}/download/{job_id}"
            
            return getDownloadResponse(
                job_id=job_id,
                status="completed",
                download_url=download_url,
            )
        
        else:
            # Production: Generate S3 presigned URL
            bucket_name = aws_creds["s3_bucket"]
            s3_key = f"results/{job_id}.mid"  # This matches the worker pattern
            
            try:
                # Check if file exists in S3
                s3_client.head_object(Bucket=bucket_name, Key=s3_key)
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    raise HTTPException(status_code=404, detail="Result file not found in S3")
                else:
                    raise HTTPException(status_code=500, detail="Error checking S3 file")
            
            # Generate presigned URL (valid for 1 hour)
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': s3_key},
                ExpiresIn=3600  # 1 hour
            )
            
            return getDownloadResponse(
                job_id=job_id,
                status="completed",
                download_url=presigned_url,
            )


    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in getDownload: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Error getting download link: {str(e)}")
    
@router.get("/download/{job_id}")
def download_file(job_id: str, db: Session = Depends(get_db)):
    """Serve file for download in local development"""
    if not local:
        raise HTTPException(status_code=404, detail="Endpoint not available in production")
    
    UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
    file_path = UPLOAD_DIR / "results" / f"{job_id}.mid"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=f"{job_id}.mid",
        media_type='application/octet-stream'
    )