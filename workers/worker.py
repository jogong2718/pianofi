import os, json, time, logging, redis, boto3
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from packages.pianofi_config.config import Config
from workers.tasks.audio_separation import separate_stems
from workers.tasks.transcription import transcribe_accompaniment, transcribe_vocals
from workers.tasks.reduction import reduce_to_piano

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

# Redis & DB
r = redis.from_url(Config.REDIS_URL, decode_responses=True)

DATABASE_URL = Config.DATABASE_URL
aws_creds = Config.AWS_CREDENTIALS
local = Config.ENVIRONMENT == "development"

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

if not local:
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_creds["aws_access_key_id"],
        aws_secret_access_key=aws_creds["aws_secret_access_key"],
        region_name=aws_creds["aws_region"],
    )

def process_job(job):
    job_id   = job["jobId"]
    file_key = job["fileKey"]
    user_id  = job["userId"]
    bucket   = Config.AWS_CREDENTIALS["s3_bucket"]
    db       = next(get_db())

    # 1) DB → status=processing
    update_sql = text("""
        UPDATE jobs
        SET status='processing', started_at=NOW() 
        WHERE job_id=:jobId AND file_key=:fileKey AND user_id=:userId
    """)

    update_result = db.execute(update_sql, {"jobId":job_id, "fileKey":file_key, "userId":user_id})

    if update_result.rowcount == 0:
        logging.error(f"Job {job_id} not found or already processed.")
        return
    logging.info(f"Job {job_id} is now processing.")

    db.commit()

    # 2) Download raw audio
    if local:
        # Local development - use a local file
        UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
        local_raw = UPLOAD_DIR / f"{job_id}.mp3"
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
            bucket,        # S3 bucket name
            file_key,      # S3 object key (like "abc123.bin")
            str(local_raw) # Local file path where to save
        )
        logging.info(f"Downloaded {local_raw}")

    # 3) Stem separation
    stems = separate_stems(str(local_raw), f"/tmp/{job_id}_stems")  

    if local:
        logging.info(f"Using local stems for job {job_id}")
    else:
        # Upload stems to S3
        for stem_name, stem_path in stems.items():
            s3_key = f"stems/{job_id}/{stem_name}.wav"
            logging.info(f"Uploading {stem_path} to s3://{bucket}/{s3_key}")
            s3_client.upload_file(stem_path, bucket, s3_key)
            stems[stem_name] = s3_key


    # 4) Transcription
    acc_mid = f"/tmp/{job_id}_acc.mid"
    voc_mid = f"/tmp/{job_id}_voc.mid"
    transcribe_accompaniment(stems["accompaniment"], acc_mid)
    transcribe_vocals(stems["vocals"], voc_mid)

    # 5) Reduction
    final_mid = f"/tmp/{job_id}_final.mid"
    reduce_to_piano([acc_mid, voc_mid], final_mid)

    # 6) Upload result
    result_key = f"results/{job_id}.mid"
    s3_client.upload_file(final_mid, bucket, result_key)

    # 7) DB → done
    db.execute(text("""UPDATE jobs SET status='done', finished_at=NOW(), result_key=:rk
                       WHERE job_id=:id"""), {"id":job_id,"rk":result_key})
    db.commit()
    db.close()
    logging.info(f"Job {job_id} completed.")

def main():
    logging.info("Worker started, waiting for jobs…")
    while True:
        item = r.brpop("job_queue", timeout=5)
        if not item:
            continue
        _, raw = item
        try:
            job = json.loads(raw)
            logging.info(f"Dequeued {job['jobId']}")
            process_job(job)
        except Exception:
            logging.exception("Error processing job; will continue.")

if __name__=="__main__":
    main()
