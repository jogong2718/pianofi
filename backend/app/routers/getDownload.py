import uuid
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List
import os
import logging

logger = logging.getLogger("uvicorn.error")

from app.config_loader import Config 
from app.schemas.getDownload import getDownloadResponse
from app.schemas.user import User
from app.auth import get_current_user
from app.database import get_db
from app.services import storage_service

router = APIRouter()

aws_creds = Config.AWS_CREDENTIALS
local = Config.USE_LOCAL_STORAGE == "true"

s3_client = None
if not local:
    s3_client = boto3.client(
        "s3",
        region_name=aws_creds["aws_region"],
    )

@router.get("/getMidiDownload/{job_id}", response_model=getDownloadResponse, tags=["jobs"])
def get_user_jobs(job_id: str, db: Session = Depends(get_db)):
    """
    Fetch a job by its unique jobId.
    This endpoint retrieves the downloadlink of a job based on the provided jobId.
    """
    try:
        backend_base = Config.BACKEND_BASE_URL or "http://localhost:8000"
        result = storage_service.generate_download_url(
            job_id=job_id,
            file_type="midi",
            s3_client=s3_client,
            aws_creds=aws_creds,
            use_local=local,
            backend_base_url=backend_base
        )
        
        return getDownloadResponse(**result)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in getDownload: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Error getting download link: {str(e)}")
    
@router.get("/getXmlDownload/{job_id}", response_model=getDownloadResponse, tags=["jobs"])
def get_user_jobs(job_id: str, db: Session = Depends(get_db)):
    """
    Fetch a job by its unique jobId.
    This endpoint retrieves the downloadlink of a job based on the provided jobId.
    """
    try:
        backend_base = Config.BACKEND_BASE_URL or "http://localhost:8000"
        result = storage_service.generate_download_url(
            job_id=job_id,
            file_type="xml",
            s3_client=s3_client,
            aws_creds=aws_creds,
            use_local=local,
            backend_base_url=backend_base
        )
        
        return getDownloadResponse(**result)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in getDownload: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Error getting download link: {str(e)}")

@router.get("/getPdfDownload/{job_id}", response_model=getDownloadResponse, tags=["jobs"])
def get_user_jobs(job_id: str, db: Session = Depends(get_db)):
    """
    Fetch a job by its unique jobId.
    This endpoint retrieves the downloadlink of a job based on the provided jobId.
    """
    try:
        if local:
            # Use absolute URL with your backend base URL
            backend_base = Config.BACKEND_BASE_URL or "http://localhost:8000"
            download_url = f"{backend_base}/downloadPdf/{job_id}"
            
            return getDownloadResponse(
                job_id=job_id,
                status="completed",
                pdf_download_url=download_url,
            )
        
        else:
            # Production: Generate S3 presigned URL
            bucket_name = aws_creds["s3_bucket"]
            s3_key = f"pdf/{job_id}.pdf"  # This matches the worker pattern

            print(bucket_name, s3_key)
            
            try:
                # Check if file exists in S3
                s3_client.head_object(Bucket=bucket_name, Key=s3_key)
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    logger.error(f"File not found in S3: {s3_key}")
                    logger.error(f"Bucket: {bucket_name}")
                    logger.error(f"Error details: {e}")
                    return getDownloadResponse(
                        job_id=job_id,
                        status="missing",
                        pdf_download_url=None,
                    )
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
                pdf_download_url=presigned_url,
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
    file_path = UPLOAD_DIR / "midi" / f"{job_id}.mid"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=f"{job_id}.mid",
        media_type='application/octet-stream'
    )

@router.get("/downloadPdf/{job_id}")
def download_pdf(job_id: str, db: Session = Depends(get_db)):
    """Serve PDF file for download in local development"""
    if not local:
        raise HTTPException(status_code=404, detail="Endpoint not available in production")
    
    UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
    file_path = UPLOAD_DIR / "pdf" / f"{job_id}.pdf"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=f"{job_id}.pdf",
        media_type='application/pdf'
    )
