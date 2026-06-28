# Pilot Customer Onboarding

Use this guide when onboarding the first commercial pilots for Thorpe Desktop **v1.1.0**.

## What pilots get today

| Capability | Status |
|------------|--------|
| Jonathan AI chat + repair approval | Ready |
| System health scan + diagnostics | Ready |
| Repair Center (Professional+) | Ready |
| PDF export (Professional+) | Ready |
| Technician Workspace (Enterprise) | Ready |
| Intelligence Console (Enterprise) | Ready |
| Stripe Subscribe flow | Ready (requires deployed license server + Stripe) |
| In-app delta updater | Not enabled — installers via Update Manager |
| Multi-device / team management | Not shipped |

## Pre-flight checklist (Thorpe team)

1. Deploy `tools/license-server/` behind HTTPS (see [license-server README](../tools/license-server/README.md))
2. Set production `THORPE_LICENSE_SIGNING_SECRET` (match desktop builds)
3. Configure Stripe products, prices, and webhook → `POST /webhooks/stripe`
4. Build installers with:
   - `THORPE_LICENSE_API_URL=https://<host>/activate`
   - `THORPE_BILLING_API_URL=https://<host>`
5. Tag release and verify: `bash scripts/verify-release.sh v1.1.0`
6. Smoke-test on a clean VM: install, activate, scan, Jonathan chat, repair approval

## Customer delivery package

Send pilots:

1. **Installer link** — https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/latest
2. **License key** — generate with `npm run license-key -- --tier PRO --group1 <ORG> --group2 2026 --group3 001`
3. **Activation steps** — open Thorpe → **Licensing & Subscription** → enter key → **Activate**
4. **Support contact** — your MSP help desk or Thorpe support channel
5. **Known limitations** — see [GA_CHECKLIST.md](./GA_CHECKLIST.md#known-pilot-limitations)

## Optional: Stripe self-serve

If billing is enabled:

1. Pilot opens **Licensing & Subscription**
2. Clicks **Subscribe** on Professional or Enterprise
3. Completes Stripe Checkout in the system browser
4. Returns to Thorpe — license auto-activates when payment confirms

Ensure `THORPE_BILLING_API_URL` points to the same host as the license server.

## Air-gapped / offline pilots

Omit `THORPE_LICENSE_API_URL` at build time. Keys validate locally via HMAC. Distribute pre-generated keys only — demo keys are blocked in release builds.

## Support runbook

| Issue | Action |
|-------|--------|
| “License invalid” | Regenerate key with matching `THORPE_LICENSE_SIGNING_SECRET` |
| “Billing not configured” | Set `THORPE_BILLING_API_URL` or use manual key activation |
| Expired license banner on Dashboard | Customer renews or receives a new key |
| Update not detected | Confirm GitHub release is public (not draft); check **Updates** page |
| SmartScreen / Gatekeeper warning | Expected for unsigned builds; provide signed build when certs are ready |

## Security notes for pilots

- No passwords are collected by Jonathan
- Mutating repairs require explicit user approval
- Cloud AI keys stay on-device (OS keychain)
- License server should use `THORPE_LICENSE_API_TOKEN` in production

## Escalation

Document pilot feedback in your issue tracker. Tag releases with pilot version (e.g. `v1.1.0-pilot1`) only for internal tracking — public tags should follow semver.
