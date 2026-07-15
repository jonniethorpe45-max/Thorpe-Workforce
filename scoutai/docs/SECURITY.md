# ScoutAI Security

**Stage 3 foundation.** This document defines security requirements and implementation boundaries for the ScoutAI modular monolith. It is binding for `apps/api`, `apps/web`, `apps/worker`, and shared packages.

## Security Objectives

1. Protect user credentials and session integrity.
2. Enforce server-side authorization for every mutating and sensitive read operation.
3. Minimize exposure of minor athlete data.
4. Maintain an append-only audit trail for security-relevant events without logging secrets.
5. Fail closed: ambiguous auth/authz results in denial, not permissive defaults.

## Authentication

### Password storage

- Passwords are hashed with **Argon2id** (preferred) or Argon2i via a well-maintained library (e.g., `@node-rs/argon2` or `argon2`).
- Plaintext passwords are never stored, logged, returned in API responses, or written to audit events.
- Password reset and verification tokens are single-use, time-limited, and stored hashed at rest (**Future** flows).

### Sessions

- Authentication uses **HTTP-only cookie sessions** issued by `apps/api`.
- Session cookies:
  - `HttpOnly: true` — not readable by JavaScript.
  - `Secure: true` in production (HTTPS only).
  - `SameSite: Lax` (default) or `Strict` where UX allows; document any cross-site embedding exceptions.
  - Scoped `Path` and optional `Domain` per deployment environment.
- Session identifiers are opaque random tokens; session payload lives server-side (PostgreSQL session table and/or Redis-backed session store per implementation).
- Logout invalidates the server-side session record and clears the cookie.
- Session fixation is prevented by rotating session ID on successful login.

### Credential handling in development

- Seed data uses fictional accounts (`@scoutai.dev`). See `DEVELOPMENT.md`.
- Developers must not use real minor or third-party credentials in local databases.

## CSRF Considerations

ScoutAI uses cookie-based sessions, which requires explicit CSRF defense for state-changing requests.

| Context | Mitigation |
| --- | --- |
| Same-site browser forms / `fetch` from `apps/web` | `SameSite` cookies + origin checks on API |
| Mutating API routes (`POST`, `PUT`, `PATCH`, `DELETE`) | Require `Origin` / `Referer` validation against allowlist, or double-submit CSRF token |
| Cross-origin SPA (if introduced later) | Token-based CSRF header or move to Bearer tokens with short TTL |

**Stage 3 baseline:** API middleware validates `Origin` (and `Referer` when present) for mutating requests from browser clients. JSON APIs reject requests with missing or mismatched origin in production.

**Non-browser clients** (CI, worker, future mobile) use separate credentials (API keys or service tokens, **Future**) and are not subject to browser CSRF rules.

## Authorization

- Authorization is enforced exclusively on the server. See `AUTHORIZATION_MATRIX.md`.
- Policies are evaluated after authentication middleware attaches `user`, `roles`, and `requestId` to request context.
- Role checks alone are insufficient for **Restricted** actions; entitlements and resource ownership must be verified (see ADR-004).
- Admin routes (`/admin/*`) require explicit `SCOUTAI_ADMIN` role; absence of role yields `403 Forbidden`, not empty data.

## Transport and Headers

Production deployments must use TLS termination (reverse proxy or platform load balancer).

Recommended response headers (via API middleware or edge):

- `Strict-Transport-Security` (HSTS)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY` or `Content-Security-Policy: frame-ancestors 'none'` for API responses
- `Referrer-Policy: strict-origin-when-cross-origin`

`apps/web` CSP is configured separately; avoid inline script violations in production builds.

## Upload Security (Future Boundary)

Stage 3 does **not** implement user file uploads. The following requirements apply when video/media upload is introduced (Stage 5+):

| Control | Requirement |
| --- | --- |
| Authentication | Upload initiation requires authenticated session or signed URL |
| Authorization | Upload scoped to user/org/resource with entitlement check |
| Content type | Allowlist MIME types; do not trust client-supplied `Content-Type` alone |
| Size limits | Enforced at API and storage gateway |
| Malware scanning | Async scan before processing (**Future**) |
| Storage | Direct-to-storage uploads via short-lived signed URLs; API never proxies large binaries |
| Processing | Worker-only transcoding; API does not execute ffmpeg or user-supplied binaries |

Until upload ships, any upload endpoints must remain unimplemented or return `501 Not Implemented`.

## Secrets Handling

| Secret type | Storage | Rules |
| --- | --- | --- |
| Database URL | Environment variable / secret manager | Never commit to git |
| Redis URL | Environment variable | Same |
| Session signing secret | Environment variable | Rotate on compromise |
| AI provider keys | Environment variable | Scoped per environment; worker/API only |
| OAuth client secrets (**Future**) | Secret manager | Not in front-end bundles |

- `.env` files are gitignored; `.env.example` contains keys only, never values.
- CI uses GitHub Actions secrets; no secrets in workflow logs.
- Structured logging must redact `Authorization`, cookies, passwords, tokens, and PII fields.
- Error responses in production omit stack traces and internal paths.

## Audit Logging

Security-relevant actions append to an **audit log** (PostgreSQL `AuditEvent` or equivalent):

| Event category | Examples |
| --- | --- |
| Authentication | `auth.login.success`, `auth.login.failure`, `auth.logout`, `auth.session.revoked` |
| Authorization | `authz.denied` (role, resource, action) |
| Account | `account.updated` (field names only, not values for sensitive fields) |
| Admin | `admin.system_info.viewed` |
| Future | `recruiter.verified`, `contact.revealed`, `data.export.requested` |

Audit records include: `requestId`, `actorUserId` (nullable), `action`, `resourceType`, `resourceId`, `ip` (hashed or truncated per privacy review), `userAgent` (truncated), `timestamp`.

Audit logs are append-only from application code; application users cannot delete or edit audit rows.

## Rate Limiting

| Surface | Stage 3 policy |
| --- | --- |
| `POST /auth/login` | Strict limit per IP + per email (e.g., 10/min IP, 5/min account) |
| `POST /auth/register` (**Future**) | Per IP + proof-of-work or CAPTCHA (**Future**) |
| General API | Moderate per-IP limit (e.g., 300/min authenticated, 60/min anonymous) |
| Admin routes | Lower limits + optional IP allowlist in production |

Rate limiting is implemented at API middleware using Redis sliding windows. When exceeded, return `429 Too Many Requests` with `Retry-After`.

## Minor Data Sensitivity

High school athletes may be under 18. Security controls account for this:

- Guardian relationships gate access to restricted fields (**Future** product enforcement).
- Recruiter access to contact info requires verification + entitlement (**Future**).
- Marketing email and notification defaults are opt-in where legally required (**Future**).
- Data retention and deletion workflows follow `PRIVACY_MODEL.md`; legal review required before production launch.

Engineering must treat any field marked `restricted` in the schema as requiring explicit policy checks, not public DTO exposure.

## Dependency Review

| Practice | Frequency |
| --- | --- |
| `pnpm audit` in CI | Every PR |
| Lockfile committed | Always (`pnpm-lock.yaml`) |
| Automated dependency updates | Renovate or Dependabot (**recommended**) |
| Critical CVE response | Patch or document accepted risk within 7 days |

Disallow packages with known critical vulnerabilities in production deploys without explicit risk acceptance recorded in `PROJECT_MANIFEST.md`.

## Incident Response (Placeholder)

Production incident playbooks (credential rotation, session revocation, breach notification) are **out of scope for Stage 3**. Before launch:

1. Define on-call and escalation contacts.
2. Document session revocation procedure (global Redis session flush + DB invalidation).
3. Engage legal counsel for breach notification obligations involving minors.

## Related Documents

- `AUTHORIZATION_MATRIX.md`
- `PRIVACY_MODEL.md`
- `TESTING.md` — auth/authz test requirements
- `adr/ADR-004-entitlement-based-feature-access.md`
