## PianoFi — Copilot instructions for contributors

This file gives focused, actionable guidance for AI coding agents working in the PianoFi monorepo. Keep suggestions concrete and limited to the repository's patterns and workflows.

1. Big picture
   - This repo is a monorepo with three main parts: `frontend/` (Next.js + TypeScript UI), `backend/` (FastAPI REST API), and worker services (`amtworkers/`, `picogenworkers/`) that perform audio→MIDI transcription and post-processing.
   - Dataflow: user uploads → pre-signed S3 upload (backend routers in `backend/app/routers/`) → backend creates a DB job and pushes to Redis → worker pulls job from Redis queue (`amt_job_queue` or `picogen_job_queue`) → worker downloads from S3, runs model, produces MIDI/XML/audio, uploads back to S3, updates DB.

2. Key files to read before changing behavior
   - backend entrypoint: `backend/app/main.py` (router wiring, health endpoint)
   - backend configuration loader: `backend/app/config_loader.py` and `packages/pianofi_config/config.py` (env vs SSM behavior)
   - worker loops: `amtworkers/worker.py` and `picogenworkers/worker.py` (job lifecycle, local vs S3 mode)
   - router implementations: `backend/app/routers/*` (createJob, uploadUrl, getDownload, webhooks, etc.)
   - frontend: `frontend/app` and `frontend/components` — `useUpload`/`useCreateJob` style hooks live in `frontend/hooks/`.

3. Environment & runtime conventions
   - Development prefers Docker Compose via the repo top-level `dev-start.sh` script (runs AWS SSO login + docker-compose up). For local single-service runs, use `uvicorn backend.app.main:app --reload --port 8000` from `backend/` and `pnpm dev` or `npm run dev` in `frontend/`.
   - Config resolution: `packages/pianofi_config/config.py` uses environment variables in development and AWS SSM Parameter Store in production. Favor reading/using `Config` when modifying runtime behavior.
   - Local worker mode: set `USE_LOCAL_STORAGE=true` to avoid S3 and use `uploads/` for artifacts; useful for fast iteration and unit tests.

4. Patterns and conventions to follow
   - DB access is raw SQL executed via SQLAlchemy engine.execute(text(...)). When editing DB interactions, preserve parameterized queries (text + parameter dict). See worker files for examples.
   - Background jobs: workers read Redis lists (`brpop 'amt_job_queue'` / `picogen_job_queue`). Jobs are JSON blobs with keys: `jobId`, `fileKey`, `userId`, `level`.
   - File keys: S3 keys use prefixes: `midi/{job_id}.mid`, `xml/{job_id}.musicxml`, `processed_audio/{job_id}.mp3` or `.wav`.
   - Error handling: workers set job status `error` on failures via SQL update; maintain that behavior when adding new failure modes so UI shows job failure.

5. Testing and quick checks
   - Unit tests: Python tests (pytest) appear in dependencies; run from the root or `backend/` with `pytest` after activating the Python environment used by the project.
   - Lint/build: Frontend uses Next.js — `npm run dev` (or `pnpm dev`) and `npm run build`. Backend uses Python; run `uvicorn` for local testing. Use Docker Compose for integrated runs.

6. Integration points and external services
   - AWS S3: upload/download of audio and artifacts. Bucket name comes from `Config.AWS_CREDENTIALS['s3_bucket']`.
   - Redis: job queue; URL comes from `Config.REDIS_URL`.
   - Database: `Config.DATABASE_URL` (development via .env, production via SSM). SQL migrations are under `backend/migrations/`.
   - Stripe and Supabase: used for auth and payments; keys come from `packages/pianofi_config/config.py` via `get_stripe_keys()` / `get_supabase_config()`.

7. Safety and scope guidance for code changes
   - Don't change deployment/security behavior (SSM/Parameter Store access, S3 bucket names) without explicit coordination. These are environment-controlled.
   - Small changes to routes, serializer shapes, or worker steps are fine; larger schema or queue changes need DB migration and coordination with the frontend hooks that expect specific keys (`result_key`, `xml_key`, `status`).

8. Examples to reference in suggestions
   - How a job is updated to processing: see `amtworkers/worker.py` lines where `UPDATE jobs SET status='processing'...` is executed.
   - How uploads are saved locally in dev: `uploads/` usage inside workers (local mode branch).
   - Router wiring example: `backend/app/main.py` includes routers like `createJob`, `uploadUrl`, `getDownload`.

If anything above is unclear or you'd like me to expand a specific section (e.g., run commands, tests to run, or add examples for common edits), tell me which part and I'll iterate.
