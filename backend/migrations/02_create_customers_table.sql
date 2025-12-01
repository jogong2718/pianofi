-- Customers table (depends on users)
CREATE TABLE public.customers (
  id uuid NOT NULL,
  stripe_customer_id text NOT NULL,
  CONSTRAINT customers_pkey PRIMARY KEY (id),
  CONSTRAINT customers_id_fkey FOREIGN KEY (id) REFERENCES public.users(id)
);
