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
import subprocess
import os

try:
    from music21 import converter, stream, meter, key, tempo, pitch
    from music21.musicxml import m21ToXml
    from music21.braille import translate
except ImportError:
    raise ImportError("music21 not installed. Run: pip install music21")

try:
    import abjad
except ImportError:
    pass

from app.config_loader import Config 
from app.schemas.createSheetMusic import SheetMusicRequest, SheetMusicResponse
from app.schemas.user import User
from app.auth import get_current_user

router = APIRouter()

DATABASE_URL = Config.DATABASE_URL
aws_creds = Config.AWS_CREDENTIALS
local = Config.USE_LOCAL_STORAGE == "true"

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
        region_name=aws_creds["aws_region"],
    )

def convert_midi_to_xml(midi_file_path: str, output_path: str) -> str:
    try:
        score = converter.parse(midi_file_path)
        
        if not score.analyze('key'):
            score.insert(0, key.KeySignature(0))
        
        output_file = f"{output_path}.musicxml"
        score.write('musicxml', fp=output_file)
        return output_file
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"XML conversion failed: {str(e)}")

def convert_midi_to_visual(midi_file_path: str, output_path: str, format: str, title: str = None, composer: str = None) -> str:
    try:
        score = converter.parse(midi_file_path)
        
        if title:
            score.insert(0, meter.MetronomeMark(title))
        if composer:
            score.insert(0, tempo.TempoIndication(composer))
        
        if not score.analyze('key'):
            score.insert(0, key.KeySignature(0))
        
        output_file = f"{output_path}.{format.lower()}"
        lily_file = f"{output_path}.ly"
        
        score.write('lily', fp=lily_file)
        
        subprocess.run([
            "lilypond", 
            f"--{format.lower()}", 
            "-o", output_path.replace(f".{format.lower()}", ""),
            lily_file
        ], check=True)
        
        if os.path.exists(lily_file):
            os.remove(lily_file)
        
        return output_file
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visual conversion failed: {str(e)}")

@router.post("/convertToXml")
async def convert_to_xml_endpoint(
    midi_file_path: str,
    output_path: str
):
    try:
        result_file = convert_midi_to_xml(midi_file_path, output_path)
        return {
            "success": True,
            "output_file": result_file,
            "format": "musicxml"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/convertToVisual")
async def convert_to_visual_endpoint(
    midi_file_path: str,
    output_path: str,
    format: str,
    title: str = None,
    composer: str = None
):
    if format.lower() not in ["pdf", "png", "svg"]:
        raise HTTPException(status_code=400, detail="Format must be pdf, png, or svg")
    
    try:
        result_file = convert_midi_to_visual(midi_file_path, output_path, format, title, composer)
        return {
            "success": True,
            "output_file": result_file,
            "format": format.lower()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))