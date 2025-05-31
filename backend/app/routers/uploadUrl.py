# app/routers/upload.py

import os
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from pathlib import Path

# app/schemas/uploadUrl.py
from app.schemas.uploadUrl import UploadUrlResponse

router = APIRouter()

# 2) Grab S3 settings from environment
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")

local = False

if not (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and AWS_REGION and S3_BUCKET):
    local = True
    UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
    UPLOAD_DIR.mkdir(exist_ok=True)


# 3) Create a boto3 S3 client
if not local:
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )

@router.post("/uploadUrl", response_model=UploadUrlResponse)
def create_upload_url():
    """
    Generate a presigned PUT URL for S3, plus a jobId and fileKey.
    The client will PUT its file directly to S3 at this URL.
    """
    try:
        if local:
            # If running locally, we won't generate a presigned URL.
            # Instead, we'll just return a local file path.
            return UploadUrlResponse(
                uploadUrl=str(UPLOAD_DIR / "local-file.bin"),
                jobId="local-job",
                fileKey="local-file.bin",
            )
        # 1) Generate a unique job ID
        job_id = str(uuid.uuid4())

        # 2) Decide on a fileKey. 
        #    You can encode the job_id into the key, or just use job_id plus a default extension.
        #    If you want the client to supply a filename or extension, 
        #    you could accept it as a query param or in the request body. For now, we’ll
        #    just pick “.bin” (or you can choose `.mp3`, `.wav`, etc. as your default).
        file_key = f"{job_id}.bin"

        # 3) Generate a presigned PUT URL that expires in, say, 1 hour (3600 seconds).
        presigned_url: str = s3_client.generate_presigned_url(
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

        return UploadUrlResponse(
            uploadUrl=presigned_url,
            jobId=job_id,
            fileKey=file_key,
        )

    except ClientError as e:
        # Some AWS error occurred (invalid credentials, missing bucket, etc.)
        raise HTTPException(status_code=500, detail=f"Could not generate presigned URL: {e}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
