# Thorpe Workforce — Staging E2E Checklist (PostgreSQL)

Use this checklist before promoting to production.

## A. Environment & deployment checks

- [ ] Staging uses PostgreSQL (not SQLite) and Redis
- [ ] `DATABASE_URL` points to staging Postgres
- [ ] Alembic migrations applied successfully (`alembic upgrade head`)
- [ ] API process starts cleanly and `/health` returns `{"status":"ok"}`
- [ ] Celery worker connected and processing tasks
- [ ] Frontend points to staging API URL

## B. Auth & workspace boundary checks

- [ ] User A signup/login succeeds
- [ ] User B signup/login succeeds
- [ ] User B cannot access User A worker/template/instance/run/chain IDs
- [ ] `GET /worker-runs/{id}` is workspace-scoped
- [ ] `GET/PATCH/POST /worker-chains/{id}` is workspace-scoped

## C. Worker platform flow

- [ ] Create worker template (draft)
- [ ] Publish template (public or marketplace) with valid config
- [ ] Install template into workspace as instance
- [ ] Run instance manually and verify run status `completed`
- [ ] Verify run summary, duration, token usage, and cost fields
- [ ] Verify worker memory keys are written and retrievable for selected scope

## D. Chain flow

- [ ] Create chain with at least 2 ordered steps
- [ ] Run chain manually with runtime input
- [ ] Verify step-by-step status and output handoff
- [ ] Verify failure branch behavior with `on_failure_next_step`

## E. Marketplace flow

- [ ] Marketplace listing shows only eligible marketplace/public templates
- [ ] Category/tag/pricing filters return expected results
- [ ] Marketplace detail by id/slug resolves correctly
- [ ] Install marketplace worker creates/updates subscription state
- [ ] Review create/update works and rating aggregates update

## F. Public worker library checks

- [ ] `/public-workers` lists only public templates
- [ ] `/public-workers/{slug}` returns expected template/reviews/tools
- [ ] Response payload does not expose private/internal template fields

## G. Seed checks

- [ ] `python scripts/seed_worker_system.py` is idempotent
- [ ] `python scripts/seed_demo.py` is idempotent for system seeds and demo data guard
- [ ] Seeded templates include:
  - [ ] Sales Outreach Worker
  - [ ] Meeting Booker Worker
  - [ ] Real Estate Deal Finder Worker

## H. Regression/quality checks

- [ ] Backend tests pass in staging CI
- [ ] Frontend lint/build pass in staging CI
- [ ] No migration drift after deploy (`alembic heads` matches expected head)
- [ ] API logs show no auth leaks or unhandled exceptions in core workflows

## I. Sign-off criteria

- [ ] All critical checklist items complete
- [ ] No P0/P1 defects open
- [ ] Release notes include known limitations and rollback plan
