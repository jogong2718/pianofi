from typing import Union


from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from app.routers import separation, transcription, midi_ops
from pydantic import BaseModel

app = FastAPI()

# mount routers
app.include_router(separation.router, prefix="/separate", tags=["separation"])
app.include_router(transcription.router, prefix="/transcribe", tags=["transcription"])
app.include_router(midi_ops.router, prefix="/midi", tags=["midi"])

@app.get("/")
async def root():
    return {"message": "Audio→MIDI service is online"}