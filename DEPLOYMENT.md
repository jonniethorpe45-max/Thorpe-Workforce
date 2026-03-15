# Thorpe Workforce Deployment Guide (Railway + Vercel)

This guide documents a production-oriented deployment path for:

- **Backend**: Railway (FastAPI + Postgres + Redis + optional worker service)
- **Frontend**: Vercel (Next.js)

It preserves existing Thorpe Workforce architecture: worker platform, marketplace, billing, analytics, onboarding, internal worker stack, and Founder OS.

---

## 1) Local development baseline

### One command

```bash
docker compose up
```

Open:

- UI: `http://localhost:3000`
- API: `http://localhost:8000`

---

## 2) Backend on Railway

## Recommended Railway service layout

Create these services in Railway:

1. **API service** (root directory: `backend`)
2. **Worker service** (root directory: `backend`)
3. **Postgres plugin**
4. **Redis plugin**

### API service settings

- **Root Directory**: `backend`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `./scripts/start_production.sh`
- **Healthcheck Path**: `/health/ready`

### Worker service settings

- **Root Directory**: `backend`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `celery -A app.tasks.celery_app.celery_app worker -l info`

### Backend required environment variables

- `ENVIRONMENT=production` (or `staging`)
- `SECRET_KEY=<secure-random-value>`
- `DATABASE_URL=<Railway Postgres URL>`
- `REDIS_URL=<Railway Redis URL>`
- `APP_BASE_URL=<frontend public URL>`
- `SUPPORT_EMAIL=<support email>`

### Backend recommended environment variables

- `TRUSTED_HOSTS=api.your-domain.com,*.up.railway.app`
- `CORS_ORIGINS=https://your-frontend-domain.com`
- `BILLING_PROVIDER=placeholder` or `stripe`
- Stripe vars when billing is enabled:
  - `STRIPE_SECRET_KEY`
  - `STRIPE_PUBLISHABLE_KEY`
  - `STRIPE_WEBHOOK_SECRET`
  - plan price IDs (`STRIPE_PRICE_ID_*`)
- Email vars when SendGrid is enabled:
  - `EMAIL_PROVIDER=sendgrid`
  - `SENDGRID_API_KEY`
  - `SENDGRID_FROM_EMAIL`

### Migrations on Railway

Run once per release (or after schema changes):

```bash
cd backend
./scripts/run_migrations.sh
```

### Initial seed on Railway (safe/idempotent)

```bash
cd backend
./scripts/seed_initial_data.sh
```

For demo seed data in staging only:

```bash
SEED_DEMO_DATA=true ./scripts/seed_initial_data.sh
```

---

## 3) Frontend on Vercel

### Project settings

- **Framework**: Next.js (auto-detected)
- **Root Directory**: `frontend`
- **Build Command**: default (`next build`)
- **Output**: default

### Required Vercel environment variables

- `NEXT_PUBLIC_API_BASE_URL=https://api.your-domain.com`
- `NEXT_PUBLIC_APP_URL=https://your-frontend-domain.com`

### Optional frontend vars

- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`
- feature flags:
  - `NEXT_PUBLIC_INTERNAL_WORKER_BUILDER_ENABLED`
  - `NEXT_PUBLIC_WORKER_CREATOR_ENABLED`

---

## 4) Staging recommendations

Use:

- `ENVIRONMENT=staging`
- Stripe **test** keys
- staging domains
- staging Postgres/Redis instances

Suggested:

- backend: `https://staging-api.your-domain.com`
- frontend: `https://staging.your-domain.com`
- `CORS_ORIGINS=https://staging.your-domain.com`
- `TRUSTED_HOSTS=staging-api.your-domain.com`

---

## 5) Production checklist

Before go-live:

1. Backend deployed and reachable
2. Postgres + Redis connected
3. `alembic upgrade head` executed
4. Initial seed executed (`seed_initial_data.sh`)
5. Frontend deployed on Vercel with correct env vars
6. Custom domains configured
7. Stripe webhook configured (if billing enabled)
8. Email provider configured and sender verified
9. Health endpoints passing:
   - `/health`
   - `/health/live`
   - `/health/ready`

---

## 6) Stripe + webhook notes

When billing is enabled:

- Webhook endpoint:
  - `POST https://api.your-domain.com/billing/webhooks/stripe`
- Use **test keys** in staging and **live keys** in production
- Ensure webhook secret matches environment

---

## 7) Email deployment notes

If using SendGrid:

- set `EMAIL_PROVIDER=sendgrid`
- set `SENDGRID_API_KEY`
- set `SENDGRID_FROM_EMAIL`
- configure SPF/DKIM/DMARC for your sending domain

---

## 8) Smoke test checklist (staging/production)

After deployment, verify:

1. Homepage loads
2. Signup works
3. Login works
4. Onboarding flow works
5. Starter marketplace workers visible
6. Worker install works
7. Worker run works
8. Founder OS pages load and chain run creates report
9. Password reset works (if email configured)
10. Support/contact flow works
11. `/health`, `/health/live`, `/health/ready` respond correctly
12. Billing page/checkouts work (if Stripe enabled)
13. Admin dashboards/routes accessible for admin users

---

## 9) Local -> staging -> production continuity

Recommended promotion path:

1. Validate locally (`docker compose up`)
2. Deploy backend to staging on Railway
3. Run migrations + staging seed
4. Deploy frontend staging on Vercel
5. Run staging smoke tests
6. Promote same config pattern to production
7. Re-run smoke tests + monitor health endpoints
