-- 1. Enable the uuid‐ossp extension (for generating UUIDs server‐side, if you want)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. The main jobs table
CREATE TABLE jobs (
  job_id        UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  file_key      TEXT        NOT NULL,
  status        TEXT        NOT NULL CHECK (status IN ('initialized','queued','processing','done','error')),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  queued_at     TIMESTAMPTZ,
  started_at    TIMESTAMPTZ,
  finished_at   TIMESTAMPTZ,
  result_key    TEXT,      -- e.g. "results/<job_id>.mid"
  error_msg     TEXT,      -- non‐null only if status='error'
  CONSTRAINT file_key_format CHECK (file_key <> '')
);

-- 3. Index on status so you can efficiently query all "queued" or "processing" jobs
CREATE INDEX idx_jobs_status ON jobs(status);

-- (Optional) If you want to enforce that `file_key` is unique per job:
ALTER TABLE jobs
  ADD CONSTRAINT unique_file_key UNIQUE (file_key);
