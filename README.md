# Thorpe Workforce MVP

Thorpe Workforce is an AI workforce operating system. This MVP ships the first worker: an **AI Sales Worker** that can orchestrate outbound campaign workflows, generate personalized outreach, and track replies/meetings.

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
- Celery tasks are wired for worker execution, approved sends, reply classification, follow-up scheduling, and analytics hooks.
- Current AI/email/calendar providers include mock implementations to keep local MVP runnable without third-party keys.
- Safe sending defaults include workspace daily cap, worker campaign cap, duplicate step prevention, and unsubscribe/bounce suppression.
