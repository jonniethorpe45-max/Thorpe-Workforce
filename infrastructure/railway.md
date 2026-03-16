# Railway deployment guide (backend + worker)

This repo is preconfigured for Railway deployments from the `backend/` directory.

## 1) Create resources

In Railway, create one project with:

- **PostgreSQL** service
- **Redis** service
- **API** service (from this GitHub repo, root directory `backend`)
- **Worker** service (same repo, root directory `backend`)

## 2) API service settings

- Root directory: `backend`
- Start command: `bash scripts/start-web.sh`
  - `backend/railway.json` already sets this and health check path (`/health/live`).
- Public domain:
  - attach `api.thorpeworkforce.ai` to the API service

Required variables on API service:

- `ENVIRONMENT=production`
- `SECRET_KEY=<strong-random-secret>`
- `DATABASE_URL` (reference Railway Postgres `DATABASE_URL`)
- `REDIS_URL` (reference Railway Redis connection URL)
- `APP_BASE_URL=https://thorpeworkforce.ai`
- `STRIPE_BILLING_PORTAL_RETURN_URL=https://thorpeworkforce.ai/app/settings/billing`
- `CORS_ORIGINS=["https://thorpeworkforce.ai","https://www.thorpeworkforce.ai"]`
- `TRUSTED_HOSTS=api.thorpeworkforce.ai,*.up.railway.app`
- `RUN_MIGRATIONS_ON_START=true`
- `RUN_SEEDS_ON_START=false` (set `true` only for first bootstrap if you want auto-seed)
- `UVICORN_HOST=::` (recommended for Railway private networking compatibility)

Optional provider vars:

- `AI_PROVIDER`, `EMAIL_PROVIDER`, `CALENDAR_PROVIDER`
- `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- Stripe vars (`BILLING_PROVIDER`, `STRIPE_*`)

## 3) Worker service settings

- Root directory: `backend`
- Start command: `bash scripts/start-worker.sh`
- No public domain needed

Required variables on Worker service:

- `ENVIRONMENT=production`
- `SECRET_KEY=<same as API service>`
- `DATABASE_URL` (same value as API service)
- `REDIS_URL` (same value as API service)
- `CELERY_LOG_LEVEL=info`

## 4) Frontend integration

Set these on the frontend host (Vercel or equivalent):

- `NEXT_PUBLIC_API_BASE_URL=https://api.thorpeworkforce.ai`
- `NEXT_PUBLIC_APP_URL=https://thorpeworkforce.ai`

## 5) DNS

Create a DNS `CNAME` for `api.thorpeworkforce.ai` pointing to the Railway target shown for your API service domain.

## 6) Verify after deploy

- `GET https://api.thorpeworkforce.ai/health`
- `GET https://api.thorpeworkforce.ai/health/live`
- `GET https://api.thorpeworkforce.ai/health/ready`

## Troubleshooting: "Failed to get private network endpoint"

If Railway shows this error during deploy/network attach:

1. Confirm API service is using `bash scripts/start-web.sh`.
2. Ensure `UVICORN_HOST=::` (or equivalent IPv6-capable bind) on the API service.
3. Redeploy the API service once, then redeploy Worker.
4. Verify both services are in the same Railway project/environment.
5. If using internal service-to-service URLs, use the Railway private domain over `http://` (not `https://`).
