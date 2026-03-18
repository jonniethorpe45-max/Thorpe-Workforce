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

Launch-readiness improvements now include:

- guided onboarding flow with persistent state (`/onboarding/*`)
- starter marketplace content (12+ launch-ready worker templates)
- featured marketplace controls for admins
- transactional email foundation (welcome, workspace ready, subscription, publish/purchase confirmation, password reset)
- password reset API flow (`/auth/forgot-password`, `/auth/reset-password`)
- support/contact intake (`/support/contact`) and admin support queue (`/support/requests`)
- legal/trust public pages and polished marketing navigation/footer
- readiness/liveness health endpoints (`/health/live`, `/health/ready`)

The current public worker remains AI Sales Worker, while the architecture supports future built-in and custom worker types.

## Thorpe Workforce Internal Worker Stack

Thorpe Workforce now includes a seeded **Internal Worker Stack** so the product can be operated by its own AI workers:

1. Chief Marketing Worker
2. User Feedback Intelligence Worker
3. Marketplace Curator Worker
4. Creator Recruitment Worker
5. Sales Outreach Worker (internal stack variant)
6. Product Strategy Worker
7. Content Marketing Worker
8. Community Manager Worker
9. Investor Update Worker
10. Operations Coordinator Worker

All 10 workers are real `worker_templates` seeds (not mock-only fixtures) and can be:

- discovered in marketplace/public worker listings
- installed into workspaces
- executed through the normal worker instance run path
- filtered together via shared tags:
  - `thorpe-workforce`
  - `internal-stack`
  - `founder-os`
  - `startup-ops`

This powers the startup narrative:
**“Thorpe Workforce is run by Thorpe Workforce AI workers.”**

Suggested internal chain recipes (workspace-level `worker_chains`):

- **Daily Founder Briefing Chain**
  - User Feedback Intelligence Worker
  - Marketplace Curator Worker
  - Operations Coordinator Worker
- **Growth Campaign Chain**
  - Product Strategy Worker
  - Chief Marketing Worker
  - Community Manager Worker
- **Investor Update Chain**
  - Operations Coordinator Worker
  - Product Strategy Worker
  - Investor Update Worker

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

## Cloud Agent Environment (Cursor)

This repo now includes a cloud-agent environment config for a test-ready full stack:

- `.cursor/environment.json`
- `.cursor/scripts/install_backend_env.sh`
- `.cursor/scripts/install_fullstack_env.sh`
- `.cursor/scripts/start_fullstack_env.sh`

On cloud-agent boot, Cursor will:

1. create `backend/.venv`
2. install Python backend dependencies from `backend/requirements.txt`
3. preinstall core backend tooling (`pytest`, `fastapi`, `uvicorn`)
4. install frontend dependencies from `frontend/package-lock.json`
5. start in a full-stack test-ready context

After startup, run validation with:

```bash
cd backend && python -m pytest
cd frontend && npm run lint
cd frontend && npm run build
```

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

## Production domain setup

Yes, the backend can run on a dedicated API subdomain.

For Thorpe Workforce production:

- Frontend site URL: `https://thorpeworkforce.ai`
- Backend API URL: `https://api.thorpeworkforce.ai`

Recommended environment values:

- `frontend/.env.local` (or frontend host env):
  - `NEXT_PUBLIC_API_BASE_URL=https://api.thorpeworkforce.ai`
  - `NEXT_PUBLIC_APP_URL=https://thorpeworkforce.ai`
- `backend/.env`:
  - `APP_BASE_URL=https://thorpeworkforce.ai`
  - `CORS_ORIGINS=["https://thorpeworkforce.ai","https://www.thorpeworkforce.ai"]`
  - `TRUSTED_HOSTS=api.thorpeworkforce.ai`

## Railway deployment

Backend Railway config has been added under `backend/`:

- `backend/railway.json` (health check + web start command)
- `backend/Procfile` (web + worker process commands)
- `backend/scripts/start-web.sh` (optional migrate/seed on boot + uvicorn)
- `backend/scripts/start-worker.sh` (celery worker)

Follow `infrastructure/railway.md` for the exact setup, including:

- API custom domain `api.thorpeworkforce.ai`
- Postgres/Redis wiring
- frontend env pointing to the API domain

Launch assistant:

- `python infrastructure/launch_assistant.py checklist`
- `python infrastructure/launch_assistant.py verify --api-url https://api.thorpeworkforce.ai --app-url https://thorpeworkforce.ai`
- full operator notes: `LAUNCH_ASSISTANT.md`

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
- Onboarding (`/onboarding/state`, `/onboarding/recommendations`)
- Support (`/support/contact`, `/support/contact/authenticated`, `/support/requests*`)
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
- `backend/migrations/versions/0009_launch_readiness.py`
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
- Onboarding is available at `/app/onboarding` and persists per user via `user_onboarding_states`.
- Public marketing/legal routes now include:
  - `/`
  - `/marketplace`
  - `/workers/*`
  - `/about`
  - `/contact`
  - `/privacy`
  - `/terms`
  - `/acceptable-use`
- Starter marketplace seeds now include real-estate, marketing, sales, research, and operations workers (12+ launch templates).
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
- `SUPPORT_EMAIL`
- `TRUSTED_HOSTS` (comma-separated, e.g. `localhost,127.0.0.1,app.example.com`)
- `PASSWORD_RESET_TOKEN_TTL_MINUTES`

Frontend env additions:

- `NEXT_PUBLIC_API_BASE_URL` (public API origin, e.g. `https://api.thorpeworkforce.ai`)
- `NEXT_PUBLIC_APP_URL` (for sitemap/robots metadata base)

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

## Launch smoke test flow

1. Open `/` and verify hero, marketplace CTA, and footer legal links.
2. Sign up at `/signup` and confirm redirect to `/app/onboarding`.
3. Complete onboarding: select goal, install starter worker, run first worker.
4. Verify dashboard shows checklist/activity and onboarding state persists.
5. Open `/app/marketplace`, filter by featured, and install a worker.
6. Open `/contact` and submit a support request.
7. As admin, review `/app/admin/support` and mark request resolved.
8. Validate `/health`, `/health/live`, and `/health/ready`.
