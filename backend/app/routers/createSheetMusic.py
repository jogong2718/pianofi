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

router = APIRouter()

DATABASE_URL = Config.DATABASE_URL
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

async def get_xml_for_job(job_id: str, user_id: str, db: Session) -> str:
    try:
        sql = text("""
            SELECT status FROM jobs 
            WHERE job_id = :job_id AND user_id = :user_id
        """)
        
        result = db.execute(sql, {
            "job_id": job_id, 
            "user_id": user_id
        }).fetchone()
        
        if not result:
            logger.error(f"Job not found or access denied: {job_id}")
            raise HTTPException(status_code=404, detail="Job not found or access denied")
        
        status = result[0]
        logger.info(f"Job status: {status} (type: {type(status)})")
        
        if status != 'done':
            logger.error(f"Job not completed. Current status: {status}")
            raise HTTPException(status_code=400, detail=f"Job not completed. Current status: {status}")
        
        s3_key = f"xml/{job_id}.musicxml"
        try:
            response = s3_client.get_object(
                Bucket=aws_creds["s3_bucket"],
                Key=s3_key
            )
            xml_content = response['Body'].read()
            return xml_content
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.error(f"MusicXML file not found in S3: {s3_key}")
                raise HTTPException(status_code=404, detail="MusicXML file not found in S3")
            else:
                logger.error(f"S3 download failed: {str(e)}")
                raise HTTPException(status_code=500, detail=f"S3 download failed: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in get_xml_for_job: {str(e)}")  # .exception() includes stack trace
        raise HTTPException(status_code=500, detail=f"XML generation failed: {str(e)}")


async def get_midi_for_job(job_id: str, user_id: str, db: Session) -> str:
    try:
        sql = text("""
            SELECT status FROM jobs
            WHERE job_id = :job_id AND user_id = :user_id
        """)
        result = db.execute(sql, {
            "job_id": job_id,
            "user_id": user_id
        }).fetchone()

        if not result:
            logger.error(f"Job not found or access denied: {job_id}")
            raise HTTPException(status_code=404, detail="Job not found or access denied")
        
        status = result[0]
        logger.info(f"Job status: {status}")
        
        if status != 'done':
            logger.error(f"Job not completed. Current status: {status}")
            raise HTTPException(status_code=400, detail=f"Job not completed. Current status: {status}")
        
        s3_key = f"midi/{job_id}.mid"
        try:
            response = s3_client.get_object(
                Bucket=aws_creds["s3_bucket"],
                Key=s3_key
            )
            midi_content = response['Body'].read()
            return midi_content
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.error(f"MIDI file not found in S3: {s3_key}")
                raise HTTPException(status_code=404, detail="MIDI file not found in S3")
            else:
                logger.error(f"S3 download failed: {str(e)}")
                raise HTTPException(status_code=500, detail=f"S3 download failed: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in get_midi_for_job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"MIDI generation failed: {str(e)}")


async def get_audio_for_job(job_id: str, user_id: str, db: Session) -> tuple[bytes, dict]:
    try:
        sql = text("""
            SELECT status, audio_metadata FROM jobs 
            WHERE job_id = :job_id AND user_id = :user_id
        """)
        
        result = db.execute(sql, {
            "job_id": job_id, 
            "user_id": user_id
        }).fetchone()
        
        if not result:
            logger.error(f"Job not found or access denied: {job_id}")
            raise HTTPException(status_code=404, detail="Job not found or access denied")
        
        status, audio_metadata = result
        logger.info(f"Job status: {status}")
        
        if status != 'done':
            logger.error(f"Job not completed. Current status: {status}")
            raise HTTPException(status_code=400, detail=f"Job not completed. Current status: {status}")
        
        # Get audio file from S3
        s3_key = f"processed_audio/{job_id}.wav"
        try:
            response = s3_client.get_object(
                Bucket=aws_creds["s3_bucket"],
                Key=s3_key
            )
            audio_content = response['Body'].read()
            return audio_content, audio_metadata
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.error(f"Audio file not found in S3: {s3_key}")
                raise HTTPException(status_code=404, detail="Audio file not found in S3")
            else:
                logger.error(f"S3 download failed: {str(e)}")
                raise HTTPException(status_code=500, detail=f"S3 download failed: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in get_audio_for_job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")


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

@router.get("/getXML/{job_id}")
async def get_xml_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        authenticated_user_id = current_user.id
        xml_content = await get_xml_for_job(job_id, authenticated_user_id, db)
        
        from fastapi.responses import Response
        return Response(
            content=xml_content,
            media_type='application/xml',
            headers={
                'Content-Disposition': f'attachment; filename="{job_id}.musicxml"'
            }
        )
        
    except Exception as e:
        logger.exception(f"Error in get_xml_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/getMIDI/{job_id}")
async def get_midi_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        authenticated_user_id = current_user.id
        midi_content = await get_midi_for_job(job_id, authenticated_user_id, db)
        
        from fastapi.responses import Response
        return Response(
            content=midi_content,
            media_type='application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{job_id}.mid"'
            }
        )
    except Exception as e:
        logger.exception(f"Error in get_midi_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/getAudio/{job_id}")
async def get_audio_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        authenticated_user_id = current_user.id
        audio_content, audio_metadata = await get_audio_for_job(job_id, authenticated_user_id, db)
        
        from fastapi.responses import Response
        import json
        
        # Return audio with metadata in headers
        headers = {
            'Content-Disposition': f'attachment; filename="{job_id}.wav"',
            'X-Audio-Metadata': json.dumps(audio_metadata) if audio_metadata else '{}'
        }
        
        return Response(
            content=audio_content,
            media_type='audio/wav',
            headers=headers
        )
        
    except Exception as e:
        logger.exception(f"Error in get_audio_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))