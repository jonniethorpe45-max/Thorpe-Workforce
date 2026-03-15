# Thorpe Workforce Launch Checklist

Use this checklist before go-live.

## Environment + secrets

- [ ] `SECRET_KEY` is set to a secure non-default value
- [ ] `DATABASE_URL` points to production Postgres
- [ ] `REDIS_URL` points to production Redis
- [ ] `APP_BASE_URL` is set to production frontend URL
- [ ] `TRUSTED_HOSTS` includes production domain(s)
- [ ] `CORS_ORIGINS` is restricted to approved origins
- [ ] `SUPPORT_EMAIL` is configured
- [ ] `EMAIL_PROVIDER` + provider credentials configured (`SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`)
- [ ] `PASSWORD_RESET_TOKEN_TTL_MINUTES` reviewed

## Billing and payments

- [ ] `BILLING_PROVIDER` configured (`stripe` for production)
- [ ] Stripe keys configured:
  - [ ] `STRIPE_SECRET_KEY`
  - [ ] `STRIPE_PUBLISHABLE_KEY`
  - [ ] `STRIPE_WEBHOOK_SECRET`
  - [ ] `STRIPE_PRICE_ID_*` values for active plans
- [ ] Billing webhook endpoint reachable: `/billing/webhooks/stripe`
- [ ] Test checkout + subscription activation flow in staging

## Database + seed

- [ ] Run migrations: `alembic upgrade head`
- [ ] Run seed: `python scripts/seed_worker_system.py`
- [ ] Verify starter marketplace templates exist (12+)
- [ ] Verify featured workers are visible in marketplace filters

## App readiness

- [ ] `/health`, `/health/live`, and `/health/ready` return success
- [ ] Signup → onboarding flow works end-to-end
- [ ] First worker install + first run succeeds
- [ ] Marketplace install (free + paid path) validated
- [ ] Contact form (`/contact`) creates support requests
- [ ] Admin support queue (`/app/admin/support`) works
- [ ] Legal pages reviewed:
  - [ ] `/privacy`
  - [ ] `/terms`
  - [ ] `/acceptable-use`

## Admin + content controls

- [ ] Admin account with `admin`/`super_admin` role confirmed
- [ ] Moderation controls verified
- [ ] Feature/unfeature worker control verified
- [ ] Starter worker quality spot-check completed

## Launch smoke test

- [ ] Public homepage and navigation render correctly on desktop + mobile
- [ ] Pricing page loads plans
- [ ] Public marketplace/worker pages load metadata and content
- [ ] Password reset request/confirm flow works
- [ ] Transactional emails are being sent (or safely mocked in non-prod)

## Post-launch monitoring

- [ ] Watch API error rates and webhook failures
- [ ] Review support queue for first 24h
- [ ] Monitor billing event logs and subscription state sync
