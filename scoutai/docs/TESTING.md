# ScoutAI Testing Strategy

**Stage 3 foundation.** This document defines the test pyramid, required Stage 3 coverage, and how to run the test suite from the pnpm/Turborepo workspace root.

## Test Pyramid

```text
                    ┌─────────┐
                    │   E2E   │  Few, high-value user journeys (Playwright)
                   ┌┴─────────┴┐
                   │ Integration │  API + DB + Redis, real Prisma migrations
                  ┌┴─────────────┴┐
                  │     Unit      │  Pure logic, policies, validators, adapters
                  └───────────────┘
```

| Layer | Scope | Tools | Location |
| --- | --- | --- | --- |
| **Unit** | Functions, policies, Zod schemas, adapter parsing | Vitest or Jest (per package convention) | `packages/*`, `apps/*/src/**/*.spec.ts` |
| **Integration** | HTTP API against test DB, session cookies, authz | Supertest + test containers or docker-compose test profile | `apps/api/test/integration/` |
| **E2E** | Browser flows through `apps/web` → `apps/api` | Playwright | `apps/web/e2e/` or `tests/e2e/` |
| **Worker** | Job processor smoke with Redis | Vitest + BullMQ test queue | `apps/worker/test/` |

## Principles

1. **Test behavior, not implementation** — assert HTTP status, response shape, and side effects (DB rows, audit events).
2. **Hermetic integration tests** — each suite uses isolated database schema or transaction rollback; no shared mutable state across tests.
3. **No real external services** — AI, video, live, and billing providers use mock adapters in CI.
4. **Deterministic seeds** — `prisma/seed.ts` produces known users for auth/authz tests.
5. **Fail CI on skip** — `@skip` or `.todo` tests are not counted toward Stage 3 exit criteria.

## Required Stage 3 Test Cases

The following cases **must** exist and pass before Stage 3 is marked verified in `PROJECT_MANIFEST.md`. Until CI has run successfully, manifest status remains **pending verification**.

### Authentication

| ID | Case | Expected |
| --- | --- | --- |
| AUTH-01 | Login with valid seed user | `200`, session cookie set (`HttpOnly`) |
| AUTH-02 | Login with invalid password | `401`, no session cookie |
| AUTH-03 | Access `GET /me` without session | `401` |
| AUTH-04 | Access `GET /me` with valid session | `200`, returns user id and roles |
| AUTH-05 | Logout clears session | Subsequent `GET /me` returns `401` |
| AUTH-06 | Password not returned in any response | Response bodies omit `passwordHash` |

### Authorization

| ID | Case | Expected |
| --- | --- | --- |
| AUTHZ-01 | Non-admin `GET /admin/system-info` | `403` |
| AUTHZ-02 | ScoutAI Admin `GET /admin/system-info` | `200`, system metadata present |
| AUTHZ-03 | `PATCH /me` cannot escalate roles | Role fields ignored or `403` |
| AUTHZ-04 | Denied admin access creates audit event | `authz.denied` row (**if audit enabled in test env**) |

### Database migrate / seed

| ID | Case | Expected |
| --- | --- | --- |
| DB-01 | `prisma migrate deploy` on clean DB | Exits 0, all migrations applied |
| DB-02 | `prisma db seed` | Creates seed users for each role class |
| DB-03 | Seed idempotency | Second seed run does not duplicate users (upsert) |

### Worker smoke

| ID | Case | Expected |
| --- | --- | --- |
| WRK-01 | Enqueue `system.smoke` job | Job completes successfully |
| WRK-02 | Worker logs structured completion | Contains `jobName`, `requestId` or `jobId` |
| WRK-03 | Worker unhealthy when Redis down | Readiness reflects dependency (**integration**) |

### Health

| ID | Case | Expected |
| --- | --- | --- |
| HLTH-01 | `GET /health` | `200`, `{ status: "ok" }` or equivalent |
| HLTH-02 | `GET /ready` with DB + Redis up | `200`, dependencies healthy |
| HLTH-03 | `GET /ready` with DB down | `503` or degraded status |

### Cross-cutting (recommended Stage 3)

| ID | Case | Expected |
| --- | --- | --- |
| X-01 | Rate limit on login (**if enabled**) | `429` after threshold |
| X-02 | Request ID in response header | `X-Request-Id` present |
| X-03 | Turbo `build` succeeds for all apps | CI build job green |

## Running Tests

All commands assume repository root (`/path/to/ScoutAI`) with Node.js 20+ and pnpm 9+.

### Prerequisites

```bash
# Start dependencies (from repo root)
docker compose up -d postgres redis

# Install and prepare database
pnpm install
cp .env.example .env   # adjust DATABASE_URL if needed
pnpm db:migrate
pnpm db:seed
```

### Commands

| Command | Purpose |
| --- | --- |
| `pnpm test` | Unit tests across workspace (Turbo) |
| `pnpm test:integration` | API integration tests (requires DB + Redis) |
| `pnpm test:e2e` | Playwright E2E (**Future** if not yet wired in Stage 3) |
| `pnpm check` | Lint + typecheck + unit tests (CI parity) |
| `pnpm build` | Production build all apps |
| `pnpm lint` | ESLint |
| `pnpm typecheck` | `tsc --noEmit` per package |

### Package-level

```bash
pnpm --filter @scoutai/api test
pnpm --filter @scoutai/api test:integration
pnpm --filter @scoutai/worker test
```

### Environment variables for tests

| Variable | Typical test value |
| --- | --- |
| `DATABASE_URL` | `postgresql://scoutai:scoutai@localhost:5432/scoutai_test` |
| `REDIS_URL` | `redis://localhost:6379/1` |
| `NODE_ENV` | `test` |
| `SESSION_SECRET` | Fixed test secret (not production value) |

Use a dedicated `scoutai_test` database; integration setup should run migrations before the suite.

## CI Integration

GitHub Actions workflow (`.github/workflows/ci.yml`) should:

1. Start Postgres + Redis service containers.
2. `pnpm install --frozen-lockfile`
3. `pnpm db:migrate`
4. `pnpm check`
5. `pnpm test:integration`
6. `pnpm build`

Test results are **not** reported as passing in `PROJECT_MANIFEST.md` until this workflow has been observed green on the Stage 3 branch.

## Coverage Targets (Guidance)

Stage 3 does not mandate coverage percentages. Prioritize:

- 100% of authorization policy functions for implemented routes
- Auth session lifecycle
- Health/ready handlers

Coverage reports may be added in Stage 4 (`pnpm test -- --coverage`).

## Related Documents

- `DEVELOPMENT.md` — local setup and seed credentials
- `SECURITY.md` — security controls under test
- `PROJECT_MANIFEST.md` — verification status
- `AI_HANDOFF.md` — what Stage 4 inherits
