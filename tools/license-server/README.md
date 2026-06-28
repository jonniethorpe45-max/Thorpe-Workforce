# Thorpe License Activation Server

Lightweight HTTP server for online license activation. The Thorpe desktop app calls this endpoint when `THORPE_LICENSE_API_URL` is set.

## Endpoint

`POST /activate`

**Request body:**

```json
{
  "license_key": "PRO-ACME-2026-A001-XXXX",
  "organization": "Acme MSP",
  "app_version": "1.1.0",
  "platform": "windows"
}
```

**Response (200):**

```json
{
  "tier": "professional",
  "expires_at": "2027-06-27T12:00:00+00:00",
  "organization": "Acme MSP"
}
```

`GET /health` returns `{"status":"ok"}`.

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `THORPE_LICENSE_SIGNING_SECRET` | dev default | Must match desktop builds |
| `THORPE_LICENSE_SERVER_HOST` | `127.0.0.1` | Bind address |
| `THORPE_LICENSE_SERVER_PORT` | `8787` | Listen port |
| `THORPE_LICENSE_TERM_DAYS` | `365` | Subscription length |
| `THORPE_LICENSE_API_TOKEN` | _(unset)_ | Optional `Authorization: Bearer` token |
| `THORPE_LICENSE_ALLOW_DEMO` | `false` | Accept demo keys (dev only) |

## Run locally

```bash
# Generate a production key (uses same secret as server)
export THORPE_LICENSE_SIGNING_SECRET="your-production-secret"
npm run license-key -- --tier PRO --group1 ACME --group2 2026 --group3 A001

# Start server
cd tools/license-server
THORPE_LICENSE_SIGNING_SECRET="$THORPE_LICENSE_SIGNING_SECRET" python3 server.py

# Point desktop app at server
export THORPE_LICENSE_API_URL="http://127.0.0.1:8787/activate"
npm run tauri:dev
```

## Desktop integration

Set `THORPE_LICENSE_API_URL` at runtime (or in the installer environment) to your hosted `/activate` URL. When set, the desktop app **requires** the server — offline HMAC validation is disabled.

For air-gapped pilots, leave `THORPE_LICENSE_API_URL` unset and distribute HMAC-signed keys generated with `npm run license-key`.

## Tests

```bash
cd tools/license-server && python3 test_server.py
```

## Production deployment

- Run behind HTTPS (reverse proxy or load balancer)
- Use a strong `THORPE_LICENSE_SIGNING_SECRET` shared only with your key-generation pipeline
- Set `THORPE_LICENSE_API_TOKEN` and terminate TLS at the edge
- Do not enable `THORPE_LICENSE_ALLOW_DEMO` in production
