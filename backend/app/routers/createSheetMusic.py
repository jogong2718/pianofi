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

# Music processing libraries
try:
    from music21 import converter, stream, meter, key, tempo, pitch
    from music21.musicxml import m21ToXml
    from music21.braille import translate
except ImportError:
    raise ImportError("music21 not installed. Run: pip install music21")

# For sheet music rendering
try:
    import abjad  # Alternative: lilypond wrapper
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
        # aws_access_key_id=aws_creds["aws_access_key_id"],
        # aws_secret_access_key=aws_creds["aws_secret_access_key"],
        region_name=aws_creds["aws_region"],
    )

def convert_midi_to_sheet_music(
    midi_file_path: str, 
    output_path: str, 
    format: str = "pdf",
    title: str = None,
    composer: str = None
) -> str:
    """
    Convert MIDI file to sheet music using music21 and LilyPond
    """
    try:
        # Load MIDI file
        score = converter.parse(midi_file_path)
        
        # Add metadata if provided
        if title:
            score.insert(0, meter.MetronomeMark(title))
        if composer:
            score.insert(0, tempo.TempoIndication(composer))
        
        # Extract piano parts
        piano_score = score
        
        # Add key signature and time signature if missing
        if not piano_score.analyze('key'):
            piano_score.insert(0, key.KeySignature(0))  # C major
        
        # Generate output based on format
        if format.lower() == "musicxml":
            output_file = f"{output_path}.musicxml"
            piano_score.write('musicxml', fp=output_file)
            
        elif format.lower() in ["pdf", "png", "svg"]:
            # Use LilyPond for high-quality sheet music rendering
            output_file = f"{output_path}.{format.lower()}"
            
            # First convert to LilyPond format
            lily_file = f"{output_path}.ly"
            piano_score.write('lily', fp=lily_file)
            
            # Then use LilyPond to render
            subprocess.run([
                "lilypond", 
                f"--{format.lower()}", 
                "-o", output_path.replace(f".{format.lower()}", ""),
                lily_file
            ], check=True)
            
            # Clean up intermediate file
            if os.path.exists(lily_file):
                os.remove(lily_file)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return output_file
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MIDI conversion failed: {str(e)}")

