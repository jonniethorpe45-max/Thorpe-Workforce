# Thorpe Workforce MVP

Thorpe Workforce is an AI workforce operating system. This MVP ships the first worker: an **AI Sales Worker** that can orchestrate outbound campaign workflows, generate personalized outreach, and track replies/meetings.

The backend is now structured as a **configuration-driven worker platform**:

- worker definitions/templates
- plan builder
- action registry
- run executor with step logs

The platform now includes a **Stripe-ready monetization layer** with:

- subscription plans and workspace subscriptions
- billing checkout + billing portal flows
- webhook-driven billing state sync
- centralized feature gating and usage limits
- paid worker entitlement checks before install/run

The current public worker remains AI Sales Worker, while the architecture supports future built-in and custom worker types.

## Monorepo Structure

```text
/frontend        # Next.js dashboard + public site
/backend         # FastAPI API + SQLAlchemy + Celery + Alembic
/infrastructure  # Infra placeholders
/docs            # Architecture docs
docker-compose.yml
```

## Tech Stack

- Frontend: Next.js App Router, React, TypeScript, Tailwind CSS
- Backend: FastAPI, SQLAlchemy, Pydantic, Alembic
- Data: PostgreSQL
- Jobs: Redis + Celery
- Auth: Email/password + JWT
- Integrations: SendGrid abstraction, Google Calendar abstraction, AI provider abstraction

## Local Development

### 1) Start infrastructure

```bash
docker compose up -d
```

### 2) Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python scripts/seed_worker_system.py
python scripts/seed_demo.py
uvicorn app.main:app --reload --port 8000
```

### 3) Run Celery worker

In another terminal:

```bash
cd backend
source .venv/bin/activate
celery -A app.tasks.celery_app.celery_app worker -l info
```

### 4) Frontend setup

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Frontend runs at `http://localhost:3000`, backend at `http://localhost:8000`.

## Demo Credentials

After running seed:

- Email: `demo@thorpeworkforce.com`
- Password: `DemoPass123!`

## Core API Coverage

Implemented endpoint groups:

- Auth (`/auth/*`)
- Workspace (`/workspace`)
- Workers (`/workers*`)
- Worker templates library (`/workers/templates/library`)
- Worker Creator drafts (`/workers/builder/*`, feature-flagged)
- Billing (`/billing/plans`, `/billing/subscription`, `/billing/checkout/*`, `/billing/portal`, `/billing/entitlements`, `/billing/webhooks/stripe`)
- Creator analytics (`/creator/dashboard/summary`, `/creator/workers`, `/creator/workers/{id}/analytics`, `/creator/payouts/summary`, `/creator/activity`)
- Workspace analytics (`/analytics/workspace/summary`, `/analytics/workspace/activity`, `/analytics/workspace/usage-history`)
- Admin analytics + moderation (`/admin/analytics/summary`, `/admin/workers*`, `/admin/creators`, `/admin/billing/summary`)
- Worker runs (`/workers/{worker_id}/runs`, `/workers/{worker_id}/execute`)
- Campaigns (`/campaigns*`)
- Leads (`/leads*`)
- Messages approval (`/messages*`, `/campaigns/{id}/messages`)
- Replies (`/replies*`)
- Meetings and calendar connect (`/meetings*`, `/calendar/connect/google`)
- Analytics (`/analytics/*`)
- Email webhooks (`/webhooks/email/*`, including unsubscribe/bounce/reply handlers)

## Migrations

Alembic migration file:

- `backend/migrations/versions/0001_initial_schema.py`
- `backend/migrations/versions/0002_worker_lifecycle_and_runs.py`
- `backend/migrations/versions/0003_worker_platform_generalization.py`
- `backend/migrations/versions/0004_template_workspace_scope.py`
- `backend/migrations/versions/0005_workforce_os_core.py`
- `backend/migrations/versions/0006_worker_creator_drafts.py`
- `backend/migrations/versions/0007_billing_core.py`
- `backend/migrations/versions/0008_analytics_ops.py`

## Tests

Run backend tests:

```bash
cd backend
pytest
```

Includes baseline coverage for:

- auth
- protected route access
- worker creation
- campaign creation
- lead import
- message generation service
- reply classification service

## Notes

- Provider abstractions are in `backend/app/integrations`.
- Worker orchestration services are in `backend/app/workers` and `backend/app/services`.
- Worker lifecycle state + run state are persisted and queryable for dashboard visibility.
- Worker behavior is assembled from `worker definition -> plan -> ordered action handlers`.
- Built-in worker template metadata is synced to `worker_templates` table on worker/template reads.
- Celery tasks are wired for worker execution, approved sends, reply classification, follow-up scheduling, and analytics hooks.
- Current AI/email/calendar providers include mock implementations to keep local MVP runnable without third-party keys.
- Safe sending defaults include workspace daily cap, worker campaign cap, duplicate step prevention, and unsubscribe/bounce suppression.
- Worker Creator is disabled by default; enable with `WORKER_CREATOR_ENABLED=true` for internal template-draft workflows.
- Billing plan seeds are idempotent and include `free`, `pro`, `creator`, and `enterprise` (plus a legacy `starter` compatibility plan).
- Server-side entitlements enforce:
  - worker builder access
  - marketplace publishing access
  - install limits
  - worker run monthly limits
  - paid worker entitlement checks
- Moderation foundation:
  - `worker_templates.moderation_status` controls public/marketplace visibility
  - users can submit template reports via `POST /workers/{worker_id}/report`
  - admins can approve/reject/hide via `POST /admin/workers/{worker_id}/moderate`
- Revenue reporting foundation:
  - creator/admin revenue values are **estimates** based on billing and marketplace events
  - payout settlement, refunds, and tax/accounting truth are intentionally separate future flows

## Stripe environment variables

Set these in `backend/.env` for Stripe-enabled billing:

- `BILLING_PROVIDER=stripe` (or keep `placeholder` for local non-payment testing)
- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ID_PRO_MONTHLY`
- `STRIPE_PRICE_ID_PRO_ANNUAL`
- `STRIPE_PRICE_ID_CREATOR_MONTHLY`
- `STRIPE_PRICE_ID_CREATOR_ANNUAL`
- `STRIPE_PRICE_ID_ENTERPRISE_MONTHLY` (optional if enterprise is sales-led)
- `APP_BASE_URL`
- `STRIPE_BILLING_PORTAL_RETURN_URL`

## Local Stripe webhook testing (Stripe CLI)

1) Start backend:

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

2) Start Stripe listener forwarding to backend:

```bash
stripe listen --forward-to localhost:8000/billing/webhooks/stripe
```

3) Copy the printed signing secret (`whsec_...`) into `STRIPE_WEBHOOK_SECRET`.

4) Trigger test events:

```bash
stripe trigger checkout.session.completed
stripe trigger customer.subscription.updated
stripe trigger invoice.paid
```

5) Verify billing sync:

- `GET /billing/subscription`
- `GET /billing/entitlements`
- check `billing_event_logs` records
