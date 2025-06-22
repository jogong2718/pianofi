import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from typing import List

# app/schemas/uploadUrl.py
from app.config_loader import Config 
from app.schemas.getJob import GetJobResponse
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

@router.get("/getJob/{job_id}", response_model=GetJobResponse, tags=["jobs"])
def get_user_jobs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Fetch all jobs for the authenticated user.
    """
    sql = text("""
        SELECT job_id, file_key as filename, status, progress, created_at as uploaded_at, output_file_key
        FROM jobs WHERE user_id = :user_id ORDER BY created_at DESC
    """)
    results = db.execute(sql, {"user_id": current_user.id}).mappings().all()
    
    jobs = []
    for row in results:
        job_data = dict(row)
        if row['status'] == 'completed' and row['output_file_key'] and s3_client:
            try:
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': aws_creds["s3_bucket"], 'Key': row['output_file_key']},
                    ExpiresIn=3600 # 1 hour
                )
                job_data['download_url'] = url
            except ClientError as e:
                print(f"Error generating presigned URL: {e}")
                job_data['download_url'] = None
        jobs.append(JobStatus.model_validate(job_data))

    return jobs