# GitHub Actions Secrets for Thorpe Desktop

Configure these in **GitHub → Settings → Secrets and variables → Actions**.

## Release signing (installers)

| Secret | Required | Description |
|--------|----------|-------------|
| `TAURI_SIGNING_PRIVATE_KEY` | Windows GA | Authenticode / Tauri signing private key |
| `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` | If key encrypted | Password for signing key |
| `APPLE_CERTIFICATE` | macOS GA | Base64-encoded `.p12` Developer ID certificate |
| `APPLE_CERTIFICATE_PASSWORD` | macOS GA | Certificate export password |
| `APPLE_SIGNING_IDENTITY` | macOS GA | e.g. `Developer ID Application: Your Org (TEAMID)` |
| `APPLE_ID` | macOS notarization | Apple ID email |
| `APPLE_PASSWORD` | macOS notarization | App-specific password |
| `APPLE_TEAM_ID` | macOS notarization | Apple Developer Team ID |

Unsigned builds work for internal testing when these are unset.

## Licensing & billing (release builds)

Set as **repository variables** or inject at installer build time:

| Secret / Variable | Required | Description |
|-----------------|----------|-------------|
| `THORPE_LICENSE_SIGNING_SECRET` | **Yes** (release) | HMAC secret for license key generation — must match license server |
| `THORPE_LICENSE_API_URL` | Commercial online activation | HTTPS URL ending in `/activate` |
| `THORPE_BILLING_API_URL` | Stripe subscriptions | HTTPS license server base URL (e.g. `https://license.thorpe.app`) |

## License server deployment (hosting)

Deploy `tools/license-server/` with these environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `THORPE_LICENSE_SIGNING_SECRET` | Yes | Same value as desktop release builds |
| `THORPE_LICENSE_API_TOKEN` | Recommended | Bearer token for `/activate` and `/checkout` |
| `STRIPE_SECRET_KEY` | Stripe billing | `sk_live_...` or `sk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe billing | Webhook signing secret from Stripe dashboard |
| `STRIPE_PRICE_PROFESSIONAL` | Stripe billing | Price ID for Professional plan |
| `STRIPE_PRICE_ENTERPRISE` | Optional | Price ID for Enterprise plan |
| `THORPE_CHECKOUT_SUCCESS_URL` | Optional | Stripe success redirect |
| `THORPE_CHECKOUT_CANCEL_URL` | Optional | Stripe cancel redirect |

### Stripe webhook endpoint

```
POST https://<your-license-server>/webhooks/stripe
```

Subscribe to `checkout.session.completed`.

## Quick setup order

1. Generate signing secret: `openssl rand -hex 32`
2. Set `THORPE_LICENSE_SIGNING_SECRET` in GitHub + license server
3. Add code signing secrets when ready for public distribution
4. Deploy license server (`docker compose up` in `tools/license-server/`)
5. Create Stripe products/prices; set `STRIPE_*` env vars
6. Tag `v1.1.0` to trigger **Thorpe Release** workflow

See also [RELEASE.md](RELEASE.md) and [GA_CHECKLIST.md](GA_CHECKLIST.md).
