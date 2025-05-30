from typing import Union
from dotenv import load_dotenv
load_dotenv()
import os
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
# from app.routers import separation, transcription, midi_ops
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# mount routers
# app.include_router(separation.router, prefix="/separate", tags=["separation"])
# app.include_router(transcription.router, prefix="/transcribe", tags=["transcription"])
# app.include_router(midi_ops.router, prefix="/midi", tags=["midi"])

origins = os.getenv("CORS_ALLOWED_ORIGINS").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] in dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Audio→MIDI service is online"}

@app.post("/uploadfile")
async def create_upload_file(
    file: UploadFile
): 
    """
    Endpoint to upload a file.
    This is just a placeholder to demonstrate file upload handling.
    """
    content = await file.read()

    # Eventually replace with S3 or other storage solution
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as f:
        f.write(content)
        
    return {"filename": file.filename, "content_type": file.content_type}