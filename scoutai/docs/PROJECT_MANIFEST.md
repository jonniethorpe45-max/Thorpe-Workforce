# ScoutAI Project Manifest

## Project Status

**Stage 3 — Repository Foundation and Build Bootstrap** (complete; published to standalone `jonniethorpe45-max/ScoutAI` repository root).

**Completion report:** [STAGE3_COMPLETION_REPORT.md](./STAGE3_COMPLETION_REPORT.md)

## Completed Work

- Governing documentation set created and populated (`PRODUCT_CONSTITUTION`, `ARCHITECTURE`, security/privacy/AI/live/video/testing/deployment/dev/handoff, authorization matrix).
- Six ADRs accepted under `docs/adr/`.
- pnpm workspaces + Turborepo monorepo scaffolding.
- Apps: `web` (Next.js), `api` (NestJS), `worker` (BullMQ).
- Shared packages: ui, database, auth, authorization, config, contracts, validation, domain, ai, video, live, billing, notifications, observability, testing.
- Prisma schema + initial migration for User, UserRole, Session, AuditEvent, Organization, OrganizationMember, Athlete, Recruiter, GuardianRelationship.
- Secure email/password auth with Argon2 hashing and HTTP-only cookie sessions.
- Authorization proof routes (`GET /me`, `GET /admin/system-info`).
- Health + readiness (Postgres + Redis).
- Worker `system.smoke` job.
- Docker Compose for Postgres/Redis + local infrastructure fallback script.
- GitHub Actions CI workflow.
- Seeded synthetic development users (not real persons / not minors).

## Current Architecture

Modular monolith:

- Next.js App Router web (`apps/web`)
- NestJS API (`apps/api`)
- BullMQ worker (`apps/worker`)
- PostgreSQL + Prisma (`packages/database`)
- Redis (queues + readiness)
- Provider adapters (mock/external-link) behind package contracts

Session strategy: database-backed sessions; raw token in HTTP-only cookie; SHA-256 token hash stored server-side; logout sets `revokedAt`.

Password hashing: Argon2 via `@scoutai/auth` (`Argon2PasswordHasher`).

## Environment Requirements

Required services: PostgreSQL 16+, Redis 7+.

Key variables (see `.env.example`):

- `DATABASE_URL`, `REDIS_URL`, `SESSION_SECRET` (≥32 chars)
- `APP_URL`, `API_URL`, `WEB_PORT`, `API_PORT`
- `COOKIE_SECURE`, `COOKIE_SAMESITE`, `LOG_LEVEL`, `NODE_ENV`

## Test Status

Commands run locally on 2026-07-15:

| Command | Result |
| --- | --- |
| `pnpm install` | Pass |
| `bash infrastructure/scripts/dev-infra-local.sh` | Pass (Postgres + Redis) |
| `pnpm db:generate` | Pass |
| Prisma migrate applied (`20260715120000_stage3_init`) | Pass |
| `pnpm db:seed` | Pass |
| `pnpm typecheck` | Pass (26 tasks) |
| `pnpm test` | Pass |
| `pnpm test:integration` | Pass — API 11/11, worker 2/2 |
| `pnpm lint` | Pass |
| `pnpm build` | Pass (includes Next.js production build) |
| Manual API smoke (`/health`, `/health/ready`, login, `/me`, admin allow/deny) | Pass |

**Note:** Docker was not available in the Stage 3 build environment. Compose files are present; local verification used host PostgreSQL/Redis via `dev-infra-local.sh`. CI is configured to use GitHub Actions service containers.

**Note:** ESLint is currently a workspace noop/`next lint` for web; deeper shared ESLint rules are pending hardening (not blocking Stage 3 gates).

## Known Issues

1. Host Docker CLI unavailable in this cloud environment — `pnpm dev:infra` falls back to local services.
2. Root ESLint config is minimal; package lint scripts mostly echo while typecheck + Next lint provide the gate.
3. Prisma `migrate reset` is blocked for AI agents without explicit user consent; initial migration was created via `prisma migrate diff` + `migrate resolve --applied` against a clean development database.

## Active Risks

- Cross-origin cookie auth between `:3000` and `:4000` requires correct CORS credentials configuration in every environment.
- Stage 4 athlete platform could accidentally expand schema too aggressively — follow constitution/stage discipline.
- Minor-athlete privacy requirements become critical as PII expands; legal review required before production collection.

## Pending Work (Stage 4)

Stage 4 — Athlete Platform Foundation:

- Athlete Passport foundation models/API/UI
- Expanded athlete profile boundaries without full product surface
- Stronger guardian relationship workflows
- Continued authorization matrix implementation

## Last Builder Handoff

See `docs/AI_HANDOFF.md`.

Do not rebuild Stage 3 foundations. Extend packages/apps with stage discipline. Keep provider abstractions intact. Update this manifest after every stage.
