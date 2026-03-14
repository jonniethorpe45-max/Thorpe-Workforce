# Thorpe Workforce MVP Architecture

Thorpe Workforce MVP is split into:

- **frontend/**: Next.js App Router dashboard and public marketing pages
- **backend/**: FastAPI API, SQLAlchemy data layer, Celery background jobs, service abstractions
- **infrastructure/**: deployment and infra placeholders

## Backend Layers

1. API Routes (`app/api/routes`)
2. Service Layer (`app/services`)
3. Orchestration Layer (`app/workers`)
4. Integrations (`app/integrations/{ai,email,calendar}`)
5. Background Tasks (`app/tasks`)
6. Persistence (`app/models`, Alembic migrations)

## AI Sales Worker State Machine

States:

- idle
- prospecting
- researching
- drafting
- awaiting_approval
- sending
- monitoring
- optimizing
- paused
- error

Core worker loop is implemented in `app/workers/executor.py`.

Worker run states:

- queued
- running
- completed
- failed
- paused

Runs are persisted in `worker_runs` and surfaced via `/workers/{worker_id}/runs`.

## Worker Loop Execution Sequence

1. Select eligible leads (suppression + duplicate checks)
2. Research leads
3. Generate outreach + follow-up drafts
4. Place drafts into approval queue
5. Send approved messages
6. Monitor webhook events
7. Classify replies
8. Update lead statuses
9. Surface interested leads for meeting booking
10. Record optimization signals

Long-running execution is queued through Celery tasks (`app/tasks/jobs.py`) with safe local fallback.

## Key Safety Defaults

- Password hashing using bcrypt via passlib
- JWT-based auth
- Basic auth route rate limiting dependency
- Manual approval for first campaign launch batch
- Do-not-contact suppression on unsubscribe/bounce
- Duplicate send suppression for same lead/sequence step
- Workspace + worker-level daily send caps
- Audit log entries for major actions
