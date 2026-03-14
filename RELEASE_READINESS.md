# Thorpe Workforce — Release Readiness

This document summarizes production hardening status for the AI Workforce OS release.

## What was built

- Configuration-driven AI Workforce OS backend:
  - Worker templates (create/update/duplicate/publish/install/list/detail)
  - Worker instances and execution engine
  - Worker runs with status, duration, token/cost telemetry
  - Worker memory service (none/instance/workspace scope)
  - Worker tools registry/runtime
  - Worker chains orchestration (manual run, step handoff, failure branching)
  - Marketplace services (listing/filtering/detail/install/reviews/revenue summary)
  - Public worker library endpoints
  - Feature-flagged Worker Creator API (`/workers/builder/*`) with draft create/edit/test/publish/unpublish/install
  - Stripe-ready monetization layer:
    - Subscription plans and workspace subscriptions
    - Stripe Checkout (workspace plans + paid worker checkout)
    - Stripe Billing Portal
    - Stripe webhook processing with idempotent event logging
    - Centralized entitlement checks and usage-limit gates
- Frontend screens:
  - Worker Builder
  - Worker Instances
  - Worker Runs
  - Worker Chains
  - Marketplace (list + detail)
  - Public Worker Library (list + detail)
  - Worker Creator UI (`/app/worker-builder`, alias redirect `/dashboard/worker-builder`)
- Idempotent system seeding for templates/tools.

## Local startup steps

### 1) Infrastructure

```bash
docker compose up -d
```

### 2) Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python scripts/seed_worker_system.py
python scripts/seed_demo.py
python -m uvicorn app.main:app --reload --port 8000
```

### 3) Celery worker (optional but recommended)

```bash
cd backend
source .venv/bin/activate
celery -A app.tasks.celery_app.celery_app worker -l info
```

### 4) Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Migration steps

```bash
cd backend
alembic upgrade head
```

Notes:
- Alembic head should resolve to `0007_billing_core`.
- Revision chain has been validated (`alembic heads`, `alembic history`).

## Seed steps

```bash
cd backend
python scripts/seed_worker_system.py
python scripts/seed_demo.py
```

System template seeds include:
- Sales Outreach Worker
- Lead Finder Worker
- Customer Support Worker
- Marketing Campaign Worker
- Meeting Booker Worker
- Real Estate Deal Finder Worker

## Required env vars

Minimum required:
- `DATABASE_URL`
- `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REDIS_URL`
- `CORS_ORIGINS`

Platform/feature vars:
- `AI_PROVIDER` (default mock)
- `EMAIL_PROVIDER` (default mock)
- `CALENDAR_PROVIDER` (default google)
- `WORKSPACE_DAILY_SEND_CAP`
- `MARKETPLACE_PLATFORM_FEE_PERCENT`
- `BILLING_PROVIDER`
- `STRIPE_SECRET_KEY`
- `INTERNAL_WORKER_BUILDER_ENABLED`
- `INTERNAL_WORKER_BUILDER_TOKEN`
- `WORKER_CREATOR_ENABLED`
- `BILLING_PROVIDER` (`placeholder` or `stripe`)
- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ID_PRO_MONTHLY`
- `STRIPE_PRICE_ID_PRO_ANNUAL`
- `STRIPE_PRICE_ID_CREATOR_MONTHLY`
- `STRIPE_PRICE_ID_CREATOR_ANNUAL`
- `STRIPE_PRICE_ID_ENTERPRISE_MONTHLY`
- `APP_BASE_URL`
- `STRIPE_BILLING_PORTAL_RETURN_URL`

## Known limitations

- Billing provider is placeholder unless Stripe integration is wired and configured.
- Chain trigger types beyond manual are scaffolded but not fully event/schedule orchestrated yet.
- Marketplace/public payloads are intentionally sanitized and do not expose internal template config internals.
- Local Docker is required for full Postgres/Redis parity checks.
- Worker Creator endpoints are intentionally hidden when `WORKER_CREATOR_ENABLED=false`.
- Alembic migrations are production-targeted for PostgreSQL; SQLite local dev is supported via ORM create_all/test fixtures, not full migration replay.
- Creator payouts are payout-ready in metadata/profile storage, but full Stripe Connect onboarding/payout automation is intentionally deferred.

## Test/verification status

- Backend tests: passing
- Frontend lint/build: passing
- Live API walkthrough: passing (signup/template publish/install/run/chain/marketplace/public)
