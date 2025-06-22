from typing import Union
from dotenv import load_dotenv
import os
from pathlib import Path
import time
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Form
from app.routers import uploadUrl, createJob, getJob  # , transcription, midi_ops
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

# mount routers
# app.include_router(separation.router, prefix="/separate", tags=["separation"])
# app.include_router(transcription.router, prefix="/transcribe", tags=["transcription"])
# app.include_router(midi_ops.router, prefix="/midi", tags=["midi"])

cors_origins = os.getenv("CORS_ALLOWED_ORIGINS")
if cors_origins:
    origins = [origin.strip() for origin in cors_origins.split(",")]
else:
    # Fallback origins for development
    origins = ["*"]  # or ["http://localhost:3000", "http://frontend:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] in dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "pianofi-backend",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {"message": "Audio→MIDI service is online"}

app.include_router(uploadUrl.router, prefix="", tags=["uploadUrl"])
app.include_router(createJob.router, prefix="", tags=["createJob"])
app.include_router(getJob.router, prefix="", tags=["getJob"])

@app.post("/uploadLocal")
async def create_upload_file(
    file: UploadFile,
    fileKey: str = Form(...),
    uploadUrl: str = Form(...)
): 
    """
    Endpoint to upload a file.
    This is just a placeholder to demonstrate file upload handling.
    """
    content = await file.read()

    UPLOAD_DIR = Path(uploadUrl)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    file_path = UPLOAD_DIR / fileKey
    with open(file_path, "wb") as f:
        f.write(content)
        
    return {"filename": file.filename, "content_type": file.content_type}