-- Jobs table (depends on users)
CREATE TABLE public.jobs (
  job_id uuid NOT NULL DEFAULT gen_random_uuid(),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  file_key text NOT NULL CHECK (file_key <> ''::text),
  status text NOT NULL CHECK (status = ANY (ARRAY['initialized'::text, 'queued'::text, 'processing'::text, 'done'::text, 'error'::text, 'deleted'::text])),
  queued_at timestamp with time zone,
  started_at timestamp with time zone,
  finished_at timestamp with time zone,
  result_key text,
  error_msg text,
  user_id uuid NOT NULL DEFAULT gen_random_uuid(),
  file_name text,
  file_size bigint,
  file_duration bigint,
  xml_key text,
  audio_metadata jsonb,
  model text,
  level integer,
  pdf_key text,
  CONSTRAINT jobs_pkey PRIMARY KEY (job_id),
  CONSTRAINT jobs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);

CREATE INDEX idx_jobs_status ON public.jobs(status);
CREATE INDEX idx_jobs_user_id ON public.jobs(user_id);
