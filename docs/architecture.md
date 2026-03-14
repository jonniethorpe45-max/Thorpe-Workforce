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

## Key Safety Defaults

- Password hashing using bcrypt via passlib
- JWT-based auth
- Basic auth route rate limiting dependency
- Manual approval for first campaign launch batch
- Do-not-contact suppression on unsubscribe/bounce
- Audit log entries for major actions
