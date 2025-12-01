-- Prices table (no dependencies)
CREATE TABLE public.prices (
  id text NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  active boolean,
  currency text,
  unit_amount bigint,
  type text,
  interval text,
  interval_count bigint,
  trial_period_days bigint,
  metadata jsonb,
  monthly_transcription_limit bigint,
  CONSTRAINT prices_pkey PRIMARY KEY (id)
);
