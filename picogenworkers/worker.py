print("starting worker...")

import json, time, logging, redis, boto3
from pathlib import Path
from sqlalchemy import create_engine, text
from packages.pianofi_config.config import Config 
from picogenworkers.tasks.picogen import run_picogen
from picogenworkers.tasks.midiToXml import convert_midi_to_xml
from picogenworkers.tasks.midiToAudio import convert_midi_to_audio
from mutagen import File
import os

print("starting worker...")

def process_job(job, engine, s3_client, aws_creds, local):
    job_id   = job["jobId"]
    file_key = job["fileKey"]
    user_id  = job["userId"]
    bucket   = aws_creds["s3_bucket"]
    # db       = next(get_db())

    # 1) DB → status=processing
    with engine.connect() as db:
        update_sql = text("""
            UPDATE jobs
            SET status='processing', started_at=NOW() 
            WHERE job_id=:jobId AND file_key=:fileKey AND user_id=:userId
        """)

        update_result = db.execute(update_sql, {"jobId":job_id, "fileKey":file_key, "userId":user_id})

        if update_result.rowcount == 0:
            logging.error(f"Job {job_id} not found or already processed.")
            return
        db.commit()
    logging.info(f"Job {job_id} status updated to processing.")
    # 2) Download raw audio
    if local:
        # Local development - use a local file
        UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
        local_raw = UPLOAD_DIR / job_id / file_key
        if not local_raw.exists():
            raise FileNotFoundError(f"Local file {local_raw} does not exist.")
        logging.info(f"Using local file {local_raw} for job {job_id}")
    else:
        # Production - download from S3
        if not s3_client:
            raise Exception("S3 client not configured for production.")
        
        local_raw = Path(f"/tmp/{job_id}.mp3")
        
        logging.info(f"Downloading s3://{bucket}/{file_key} to {local_raw}")
        s3_client.download_file(
            bucket,
            file_key,
            str(local_raw)
        )
        logging.info(f"Downloaded {local_raw}")

    # Extract audio duration
    try:
        # Load audio file to get duration
        audio = File(local_raw)
        duration = audio.info.length
        
        # Update job with file duration
        with engine.connect() as db:
            db.execute(text("""
                UPDATE jobs 
                SET file_duration = :duration 
                WHERE job_id = :job_id
            """), {"duration": duration, "job_id": job_id})
            db.commit()
    except Exception as e:
        logging.warning(f"Could not extract duration for {job_id}: {e}")

    # 3) picogen processing
    logging.info(f"Running picogen for job {job_id} on {local_raw}")
    midi_path = run_picogen(str(local_raw), f"/tmp/{job_id}_midi")  
    final_mid = midi_path
    # 4) Upload result
    midi_key = f"midi/{job_id}.mid"

    if local:
        UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
        final_mid = UPLOAD_DIR / midi_key

        if not final_mid.parent.exists():
            final_mid.parent.mkdir(parents=True, exist_ok=True)
        logging.info(f"Saving result to local {final_mid}")

        # Save the MIDI file locally
        with open(final_mid, "wb") as f:
            with open(midi_path, "rb") as midi_file:
                f.write(midi_file.read())

    else:
        # Production - upload to S3
        logging.info(f"Uploading result to s3://{bucket}/{midi_key}")
        s3_client.upload_file(final_mid, bucket, midi_key)

    # 5) Transform midi into xml

    xml_path = f"/tmp/{job_id}.musicxml"
    xml_key = f"xml/{job_id}.musicxml"

    try:
        # Use the modular conversion function
        with engine.connect() as db:
            result = db.execute(
                text("SELECT file_name FROM jobs WHERE job_id = :job_id"),
                {"job_id": job_id}
            )
            sheet_music_title = result.scalar()  # Get the single result
            logging.info(f"Sheet music title from DB: {sheet_music_title}")
            if sheet_music_title:
                sheet_music_title = os.path.splitext(sheet_music_title)[0]
                logging.info(f"Processed sheet music title: {sheet_music_title}")

        logging.info(f"Converting MIDI file: {final_mid}")
        if isinstance(final_mid, Path):
            midi_file_path = final_mid
        else:
            midi_file_path = Path(final_mid)
        
        if not midi_file_path.exists():
            logging.error(f"MIDI file does not exist: {midi_file_path}")
            return
        
        file_size = midi_file_path.stat().st_size
        logging.info(f"MIDI file size: {file_size} bytes")
        
        if file_size == 0:
            logging.error(f"MIDI file is empty: {midi_file_path}")
            return

        convert_midi_to_xml(final_mid, xml_path, job_id, sheet_music_title)

        if local:
            xml_final = UPLOAD_DIR / f"xml/{job_id}.musicxml"
            if not xml_final.parent.exists():
                xml_final.parent.mkdir(parents=True, exist_ok=True)
            with open(xml_final, "wb") as f:
                with open(xml_path, "rb") as xml_file:
                    f.write(xml_file.read())
            xml_key = f"xml/{job_id}.musicxml"
        else:
            s3_client.upload_file(xml_path, bucket, xml_key)
            xml_key = f"xml/{job_id}.musicxml"
    except Exception as e:
        logging.error(f"Error in XML conversion step for job {job_id}: {e}")
        # You might want to set job status to 'failed' here
        with engine.connect() as db:
            update_sql = text("""
                UPDATE jobs
                SET status='error', finished_at=NOW()
                WHERE job_id=:jobId
            """)
            db.execute(update_sql, {"jobId": job_id})
            db.commit()
        return
    
    # 6) Convert MIDI to audio
    audio_path = f"/tmp/{job_id}.wav"
    audio_key = f"processed_audio/{job_id}.wav"
    try:
        audio_file_path, metadata = convert_midi_to_audio(Path(final_mid), Path(audio_path), job_id)
        
        logging.info(f"Audio file generated at {audio_file_path} with metadata: {metadata}")

        if local:
            audio_final = UPLOAD_DIR / f"processed_audio/{job_id}.wav"
            if not audio_final.parent.exists():
                audio_final.parent.mkdir(parents=True, exist_ok=True)
            with open(audio_final, "wb") as f:
                with open(audio_path, "rb") as audio_file:
                    f.write(audio_file.read())

            with engine.connect() as db:
                db.execute(text("""
                    UPDATE jobs 
                    SET audio_metadata = :audio_metadata 
                    WHERE job_id = :job_id
                """), {"audio_metadata": json.dumps(metadata), "job_id": job_id})
                db.commit()
        else:
            audio_key = f"processed_audio/{job_id}.wav"
            s3_client.upload_file(audio_path, bucket, audio_key)

            with engine.connect() as db:
                db.execute(text("""
                    UPDATE jobs 
                    SET audio_metadata = :audio_metadata 
                    WHERE job_id = :job_id
                """), {"audio_metadata": json.dumps(metadata), "job_id": job_id})
                db.commit()

            audio_final = f"s3://{bucket}/{audio_key}"
    except Exception as e:
        logging.error(f"Error converting MIDI to audio for job {job_id}: {e}")
        # You might want to set job status to 'failed' here
        with engine.connect() as db:
            update_sql = text("""
                UPDATE jobs
                SET status='error', finished_at=NOW()
                WHERE job_id=:jobId
            """)
            db.execute(update_sql, {"jobId": job_id})
            db.commit()
        return

    # 7) DB → status=done, file_key=midi_key, xml_key=xml_key
    with engine.connect() as db:
        update_sql = text("""
            UPDATE jobs
            SET status='done', finished_at=NOW(), result_key=:midi_key, xml_key=:xml_key
            WHERE job_id=:jobId
        """)
        db.execute(update_sql, {
            "midi_key": midi_key,
            "xml_key": xml_key,
            "jobId": job_id,
        })
        db.commit()
    logging.info(f"Job {job_id} completed successfully. MIDI: {midi_key}, XML: {xml_key}")

    # 8) Cleanup temporary files
    try:
        for path in [Path(local_raw), Path(audio_path), Path(midi_path), Path(xml_path)]:
            if path.exists():
                path.unlink()
                logging.info(f"Deleted temporary file: {path}")
    except Exception as e:
        logging.error(f"Error cleaning up temporary files: {e}")

def main():

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    logging.info("Worker starting up...")

    aws_creds = Config.AWS_CREDENTIALS
    local = Config.USE_LOCAL_STORAGE == "true"

    try:
        logging.info("Loading configuration for redis...")
        # Redis & DB
        r = redis.from_url(Config.REDIS_URL, decode_responses=True)
        r.ping()  # Test connection
        logging.info("Connected to Redis successfully.")

        DATABASE_URL = Config.DATABASE_URL
        logging.info(f"Using database URL: {DATABASE_URL}")
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=1,
            max_overflow=2
        )

        # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # def get_db():
        #     db = SessionLocal()
        #     try:
        #         yield db
        #     finally:
        #         db.close()

        s3_client = None
        if not local:
            s3_client = boto3.client(
                "s3",
                # aws_access_key_id=aws_creds["aws_access_key_id"],
                # aws_secret_access_key=aws_creds["aws_secret_access_key"],
                region_name=aws_creds["aws_region"],
            )

    except Exception as e:
        logging.error(f"FATAL Error initializing worker: {e}")
        return

    logging.info("Worker started, waiting for jobs…")
    loop_count = 0
    try:
        while True:
            loop_count += 1
            logging.info(f"Loop iteration {loop_count}")
            try:
                item = r.brpop("picogen_job_queue", timeout=50)
                if item:
                    logging.info(f"Got job: {item}")
                    _, raw = item
                    try:
                        job = json.loads(raw)
                        logging.info(f"Dequeued {job['jobId']}")
                        process_job(job, engine, s3_client, aws_creds, local)
                    except Exception:
                        logging.exception("Error processing job; will continue.")
                else:
                    logging.info("No jobs in queue, waiting…")
                    time.sleep(1)
            except redis.exceptions.ConnectionError as e:
                logging.error(f"Redis connection error: {e}")

    except KeyboardInterrupt:
        logging.info("Worker stopped by user.")

if __name__=="__main__":
    main()