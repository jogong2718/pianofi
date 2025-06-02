# app/routers/upload.py

import os
import uuid
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session

load_dotenv()
# app/schemas/uploadUrl.py
from app.schemas.uploadUrl import UploadUrlResponse

router = APIRouter()

# 2) Grab S3 settings from environment
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")
DATABASE_URL = os.getenv("DATABASE_URL")

local = False

if not (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and AWS_REGION and S3_BUCKET):
    local = True
    UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
    UPLOAD_DIR.mkdir(exist_ok=True)

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

# 3) Create a boto3 S3 client
if not local:
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )



@router.post("/uploadUrl", response_model=UploadUrlResponse)
def create_upload_url(db: Session = Depends(get_db)):
    """
    Generate a presigned PUT URL for S3, plus a jobId and fileKey.
    The client will PUT its file directly to S3 at this URL.
    """
    try:
        job_id = str(uuid.uuid4())
        file_key = f"{job_id}.bin"

        sql = text("""
            INSERT INTO jobs (job_id, file_key, status)
            VALUES (:job_id, :file_key, 'initialized')
        """)

        db.execute(sql, {"job_id": job_id, "file_key": file_key})
        if local:
            upload_url = str(UPLOAD_DIR / f"{job_id}.bin")
        else:
            upload_url: str = s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": S3_BUCKET,
                    "Key": file_key,
                    # If you want the client to set content‐type themselves, omit ContentType here.
                    # Otherwise, you can force a content type:
                    # "ContentType": "audio/mpeg"
                },
                ExpiresIn=3600,
                HttpMethod="PUT",
            )

        db.commit()
        
        return UploadUrlResponse(
            uploadUrl=upload_url,
            jobId=job_id,
            fileKey=file_key,
        )

    except ClientError as e:
        db.rollback()
        # Some AWS error occurred (invalid credentials, missing bucket, etc.)
        raise HTTPException(status_code=500, detail=f"Could not generate presigned URL: {e}")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
