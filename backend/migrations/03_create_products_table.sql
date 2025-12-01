-- Products table (no dependencies)
CREATE TABLE public.products (
  id text NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  active boolean,
  name text,
  description text,
  image text,
  metadata jsonb,
  CONSTRAINT products_pkey PRIMARY KEY (id)
);
