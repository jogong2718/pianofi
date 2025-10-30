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
import subprocess
import os
import logging
import sys

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
from app.database import get_db

router = APIRouter()

aws_creds = Config.AWS_CREDENTIALS
local = Config.USE_LOCAL_STORAGE == "true"

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)

s3_client = None
if not local:
    s3_client = boto3.client(
        "s3",
        region_name=aws_creds["aws_region"],
    )

# Helper functions moved to sheet_music_service.py

@router.post("/convertToXml")
async def convert_to_xml_endpoint(
    midi_file_path: str,
    output_path: str
):
    try:
        from app.services import sheet_music_service
        result_file = sheet_music_service.convert_midi_to_xml(midi_file_path, output_path)
        return {
            "success": True,
            "output_file": result_file,
            "format": "musicxml"
        }
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
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
        from app.services import sheet_music_service
        result_file = sheet_music_service.convert_midi_to_visual(midi_file_path, output_path, format, title, composer)
        return {
            "success": True,
            "output_file": result_file,
            "format": format.lower()
        }
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/getXML/{job_id}")
async def get_xml_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download MusicXML file for a completed transcription job."""
    try:
        from fastapi.responses import Response
        from app.services import sheet_music_service
        
        # Call service layer
        xml_content = sheet_music_service.get_xml_file(
            job_id=job_id,
            user_id=current_user.id,
            db=db,
            s3_client=s3_client,
            aws_creds=aws_creds
        )
        
        # Wrap in HTTP response with appropriate headers
        return Response(
            content=xml_content,
            media_type='application/xml',
            headers={
                'Content-Disposition': f'attachment; filename="{job_id}.musicxml"'
            }
        )
        
    except PermissionError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Error in get_xml_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/getMIDI/{job_id}")
async def get_midi_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download MIDI file for a completed transcription job."""
    try:
        from fastapi.responses import Response
        from app.services import sheet_music_service
        
        # Call service layer
        midi_content = sheet_music_service.get_midi_file(
            job_id=job_id,
            user_id=current_user.id,
            db=db,
            s3_client=s3_client,
            aws_creds=aws_creds
        )
        
        # Wrap in HTTP response with appropriate headers
        return Response(
            content=midi_content,
            media_type='application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{job_id}.mid"'
            }
        )
        
    except PermissionError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Error in get_midi_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/getAudio/{job_id}")
async def get_audio_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download processed audio file for a completed transcription job."""
    try:
        from fastapi.responses import Response
        from app.services import sheet_music_service
        import json
        
        # Call service layer
        audio_content, audio_metadata = sheet_music_service.get_audio_file(
            job_id=job_id,
            user_id=current_user.id,
            db=db,
            s3_client=s3_client,
            aws_creds=aws_creds
        )
        
        # Return audio with metadata in headers
        headers = {
            'Content-Disposition': f'attachment; filename="{job_id}.mp3"',
            'X-Audio-Metadata': json.dumps(audio_metadata) if audio_metadata else '{}'
        }
        
        return Response(
            content=audio_content,
            media_type='audio/wav',
            headers=headers,
        )
        
    except PermissionError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Error in get_audio_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))