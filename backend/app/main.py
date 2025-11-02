from typing import Union
from dotenv import load_dotenv
import os
from pathlib import Path
import time
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Form
from app.routers import uploadUrl, createJob, getUserJobs, createSheetMusic, createCheckoutSession, webhooks, getDashboardMetrics, updateProfile, deleteJob, updateJob  # , transcription, midi_ops
from fastapi.middleware.cors import CORSMiddleware
from app.config_loader import Config

load_dotenv()

app = FastAPI()

origins = Config.CORS_ORIGINS


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] in dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Audio-Metadata"]
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
app.include_router(getUserJobs.router, prefix="", tags=["getUserJobs"])
app.include_router(createSheetMusic.router, prefix="", tags=["createSheetMusic"])
app.include_router(createCheckoutSession.router, prefix="", tags=["createCheckoutSession"])
app.include_router(webhooks.router, prefix="", tags=["webhooks"])
app.include_router(getDashboardMetrics.router, prefix="", tags=["getDashboardMetrics"])
app.include_router(updateProfile.router, prefix="", tags=["updateProfile"])
app.include_router(deleteJob.router, prefix="", tags=["deleteJob"])
app.include_router(updateJob.router, prefix="", tags=["updateJob"])