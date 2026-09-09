# AGENTS.md

Notes for AI agents (and humans) working in the PianoFi repo. These are
hard-won, project-specific gotchas — read them before touching the backend,
Stripe, Docker, or the local dev environment.

## Repo layout

- `frontend/` — Next.js 16 (App Router, Turbopack), TypeScript, Tailwind,
  shadcn/ui, `next-themes` (dark mode via `class`).
- `backend/` — FastAPI app (`app.main:app`), served by uvicorn on port 8000.
- `packages/pianofi_config/` — shared config module (`config.py`) + `.env`.
- `amtworkers/`, `picogenworkers/`, `ptiworkers/` — GPU/model workers.
- `docker-compose.yaml` — dev orchestration. `dev-start.sh` — SSO + compose.

## Local development workflow

The supported dev flow is Docker Compose, but there are important caveats.

### Starting services (frontend + backend only, no workers)

```bash
# 1. AWS SSO login is required because the backend reads some config from
#    AWS SSM Parameter Store (see config.py). Tokens expire — re-run often.
aws sso login --profile jonny-dev
cp ~/.aws/sso/cache/* project-aws/sso/cache/
cp ~/.aws/config project-aws/

# 2. Bring up ONLY frontend + backend (workers need GPU / are heavy)
docker compose -f docker-compose.yaml up --build frontend backend
```

`dev-start.sh` does the SSO + compose steps for you.

### KNOWN ISSUE: frontend Docker container crashes (Node version)

`frontend/Dockerfile.dev` uses `node:18-alpine`, but Next.js 16 requires
Node `>=20.9.0`. The frontend container exits immediately with a version error.

Workarounds:
- Run the frontend locally instead of in Docker (recommended for now):
  ```bash
  cd frontend
  NEXT_PUBLIC_BACKEND_URL=http://localhost:8000 npm run dev
  ```
- OR fix `frontend/Dockerfile.dev` to use `node:20-alpine` (or newer).

### Backend base URL

- `frontend/.env.local` sets `NEXT_PUBLIC_BACKEND_URL` to the **production AWS
  ALB**. When running the frontend locally against a local backend, override it:
  `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000 npm run dev`.
- `docker-compose.yaml` already overrides it to `http://localhost:8000` for the
  frontend service.
- Next.js inlines `NEXT_PUBLIC_*` at compile time. A shell env var set on the
  `npm run dev` command wins over `.env.local` for that process.

## Docker: code changes do NOT hot-reload reliably

This burned a lot of time. The Dockerfiles `COPY` source into the image at
build time. Neither of these reliably gets your latest code into the running
container:

- `docker compose --watch` sync — observed to silently NOT apply edits.
- `docker compose cp file container:/path` — works, BUT is **ephemeral**: it is
  wiped the next time the container is recreated (e.g. by `up -d`), reverting to
  the image's baked-in (old) code.

**Always rebuild the image after backend code changes:**

```bash
docker compose up -d --no-deps --build backend
```

Verify the running container actually has your change:

```bash
docker compose exec -T backend sh -c "grep -n 'YOUR_CHANGE' /app/app/..."
```

## Config & environment (`packages/pianofi_config/config.py`)

- Config values are loaded via `@lru_cache`d functions at import time. Changing
  `.env` requires **recreating** the container (`docker compose up -d`), not
  just `docker compose restart` (restart reuses the old env/process).
- The config only branches on `ENVIRONMENT == "staging"` vs. everything else:
  - `staging` → read secrets from **`.env`** (local/test values).
  - anything else (**including `development`**) → read from **AWS SSM Parameter
    Store**, which returns **PRODUCTION / LIVE** values.
- FOOTGUN: `ENVIRONMENT=development` does NOT mean "local". It falls through to
  the production branch and pulls **live** credentials (including the **live
  Stripe key**). For local dev use `ENVIRONMENT=staging` so the backend uses the
  test keys from `.env`.
  - TODO worth doing: add an explicit `development` branch in `config.py` that
    reads from `.env`, so `development` stops silently meaning "use live prod".

## Stripe

- Modes must match: frontend `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` (`pk_test_…`)
  and backend `STRIPE_SECRET_KEY` (`sk_test_…`) must be the **same mode**
  (test vs live) and same account. A mismatch produces confusing
  `No such price` / `No such customer` errors.
- Price IDs are mode/account-specific: a price created in test mode does NOT
  exist in live mode. Never hardcode one in shared source.
  - The upgrade modal reads `NEXT_PUBLIC_LAUNCH_PRICE_ID` and **falls back to
    the LIVE price** so production is safe if the var is unset.
  - Local dev overrides it in `frontend/.env.local` with the test-mode price.
  - Restart `npm run dev` after changing it — `NEXT_PUBLIC_*` is inlined at
    compile time.
  Verify a price exists before using it:
  ```bash
  SK=$(grep '^STRIPE_SECRET_KEY=' packages/pianofi_config/.env | cut -d= -f2-)
  curl -s "https://api.stripe.com/v1/prices/PRICE_ID" -u "$SK:"
  ```
- Known valid TEST recurring prices (account `…BHhIoAIsYd…`):
  - `price_1SQKe8BHhIoAIsYdD1lEjav1` — Launch Plan, $4.99 CAD/mo
  - `price_1Rgbv3BHhIoAIsYdP9R8hMpa` — Starter Plan, $9.00 CAD/mo
  - `price_1RgbvaBHhIoAIsYdK7GAZW7h` — Pro Plan, $29.00 CAD/mo
- Known valid LIVE recurring prices (account `…BORHHlKrvY…`):
  - `price_1SQY6fBORHHlKrvYfRPevIWq` — Launch Plan, $4.99 CAD/mo
  - `price_1SQY6oBORHHlKrvYIII2ChFt` — Starter Plan, $9.00 CAD/mo
  - `price_1SQY6nBORHHlKrvYLNfVuhGx` — Pro Plan, $29.00 CAD/mo
- Stored `stripe_customer_id`s are also mode-specific. `_get_or_create_customer`
  now verifies the stored customer exists in the current mode and recreates it
  if not (handles live↔test switches). Keep that guard.
- Checkout UI modes (account is on API `2025-05-28.basil`):
  - `ui_mode: "custom"` (Elements + Checkout Sessions API) is GA on this account
    — the "requires beta access" note in the `@stripe/stripe-js` types is stale.
    Returns a `client_secret` for `CheckoutProvider`/`PaymentElement`.
  - `ui_mode: "elements"` is the NEWER name and requires API `2026-03-25.dahlia`.
    If you upgrade the Stripe API version, rename `custom` → `elements`.
- Test card: `4242 4242 4242 4242`, any future expiry, any CVC/postal code.
- Payment UI lives in-app at `frontend/app/checkout/page.tsx` (themed, dynamic
  dark/light via Stripe Appearance API + `checkout.changeAppearance()`).
  The upgrade modal (`frontend/components/ui/upgradeModal.tsx`) routes to
  `/checkout?priceId=…`.

## Frontend conventions

- Use theme tokens (`bg-background`, `text-foreground`, `border-border`,
  `text-primary`, `text-muted-foreground`), NOT hardcoded colors like
  `bg-white`, so dark mode works.
- shadcn/ui components live in `frontend/components/ui/`. Reuse `Card`, `Button`,
  `Alert`, `Header`, etc. Match existing pages (e.g. `app/login/page.tsx`).
- Dependency installs need `--legacy-peer-deps` (pre-existing `@tonejs/piano`
  wants `tone@^14` while the project uses `tone@15`).
- `npx tsc --noEmit` has pre-existing errors in unrelated files (`form.tsx`
  react-hook-form imports, `usePlayback.tsx`, etc.). When verifying your change,
  grep tsc output for the specific files you touched rather than expecting a
  clean run.

## Verifying backend changes end-to-end

The `/createCheckoutSession` endpoint is auth-guarded (403 without a Supabase
token), so you usually can't call it directly from the CLI. Useful techniques:

- Reproduce the Stripe call directly with the account key (isolates Stripe-side
  errors like bad price/customer) — see the curl snippet above.
- Tail backend logs while triggering the action from the browser:
  ```bash
  docker compose logs backend --since 1m | grep -iE "ui_mode=|HTTP|error|No such"
  ```
- Surface real errors to the client. The checkout page reads the FastAPI
  `detail` field from non-OK responses instead of showing a generic message —
  keep error surfacing so failures aren't silent blank pages.

## Health checks

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health   # backend
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000          # frontend
docker compose ps                                                     # status
```
