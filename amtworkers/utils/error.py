from sqlalchemy import text

def mark_job_as_error(engine, job_id, error_message):
    """Mark a job as errored in the database."""
    with engine.connect() as db:
        update_sql = text("""
            UPDATE jobs
            SET status='error', finished_at=NOW(), error_msg=:errorMessage
        WHERE job_id=:jobId
    """)
    db.execute(update_sql, {"jobId": job_id, "errorMessage": error_message})
    db.commit()