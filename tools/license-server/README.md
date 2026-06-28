# Thorpe License + Billing Server

HTTP service for Thorpe Desktop **license activation** and **Stripe subscription checkout**.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Health + `stripe_configured` flag |
| `POST` | `/activate` | Validate license key (desktop `THORPE_LICENSE_API_URL`) |
| `POST` | `/checkout` | Create Stripe Checkout session |
| `GET` | `/checkout/{id}/status` | Poll for issued license key |
| `POST` | `/webhooks/stripe` | Stripe webhook (`checkout.session.completed`) |

## Desktop environment variables

| Variable | Purpose |
|----------|---------|
| `THORPE_LICENSE_API_URL` | `https://host/activate` — online activation |
| `THORPE_BILLING_API_URL` | `https://host` — Stripe checkout + polling |
| `THORPE_LICENSE_SIGNING_SECRET` | Must match server secret |

## Run locally

```bash
export THORPE_LICENSE_SIGNING_SECRET="your-production-secret"
npm run license-key -- --tier PRO --group1 ACME --group2 2026 --group3 A001

cd tools/license-server
python3 server.py
```

Desktop dev:

```bash
export THORPE_BILLING_API_URL="http://127.0.0.1:8787"
export THORPE_LICENSE_API_URL="http://127.0.0.1:8787/activate"
npm run tauri:dev
```

## Docker

```bash
cd tools/license-server
cp .env.example .env  # edit secrets
docker compose up --build
```

## Fly.io

```bash
cd tools/license-server
fly launch --no-deploy
fly secrets set THORPE_LICENSE_SIGNING_SECRET=... STRIPE_SECRET_KEY=... STRIPE_WEBHOOK_SECRET=...
fly volumes create license_data --size 1
fly deploy
```

Set desktop builds to `https://<app>.fly.dev/activate` and `https://<app>.fly.dev`.

## Railway

1. Create a new Railway project from this directory (`tools/license-server`)
2. Add a persistent volume mounted at `/data`
3. Set secrets from `.env.example`
4. Deploy — health check uses `GET /health`

## Rate limiting

Per-IP rate limits apply to all endpoints (default: 120 requests / 60 seconds). Tune with:

- `THORPE_LICENSE_RATE_LIMIT` — max requests per window (`0` disables)
- `THORPE_LICENSE_RATE_WINDOW_SEC` — window length in seconds

## Stripe setup

1. Create **Professional** and **Enterprise** recurring prices in Stripe
2. Set environment variables:

```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PROFESSIONAL=price_...
STRIPE_PRICE_ENTERPRISE=price_...
```

3. Configure webhook: `POST https://<host>/webhooks/stripe` → `checkout.session.completed`
4. Set success URL template (optional):

```bash
THORPE_CHECKOUT_SUCCESS_URL="https://thorpe.app/licensing?checkout=success&session_id={CHECKOUT_SESSION_ID}"
```

After payment, the desktop app polls `/checkout/{session_id}/status` and auto-activates the returned license key.

## Security

- Use `THORPE_LICENSE_API_TOKEN` and send `Authorization: Bearer <token>` from trusted clients
- Never commit `THORPE_LICENSE_SIGNING_SECRET`
- Do not enable `THORPE_LICENSE_ALLOW_DEMO` in production

## Tests

```bash
cd tools/license-server && python3 test_server.py
```

See [docs/GITHUB_SECRETS.md](../../docs/GITHUB_SECRETS.md) for full secret inventory.
