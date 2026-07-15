# ScoutAI Stage 4 AI Handoff

**Audience:** AI builder or engineering team implementing **Stage 4 — Athlete Platform Foundation**.  
**From:** Stage 3 repository foundation builder.  
**Date context:** Stage 3 completion handoff.

## Mission of Stage 3

Stage 3 delivered a **production-oriented repository foundation** for ScoutAI — a sports recruiting intelligence platform (US high school football first, multi-sport later). Stage 3 is **not** the athlete product surface. It establishes the modular monolith, security baseline, documentation, and CI so Stage 4 can build features without re-architecting.

## What Stage 3 Delivered

### Repository and workspace

- pnpm workspace + Turborepo monorepo
- `apps/web` (Next.js App Router), `apps/api` (NestJS), `apps/worker` (BullMQ)
- Shared `packages/*` for auth, database, config, contracts, ai, live, video, testing, observability

### Data and persistence

- PostgreSQL as system of record via Prisma
- Schema foundations: `User`, roles, `Session`, `AuditEvent`, organization, athlete, recruiter, guardian relationship stubs
- Migrations and idempotent seed script with fictional `@scoutai.dev` users

### Authentication and authorization

- Email/password auth with **Argon2** password hashing
- **HTTP-only cookie sessions** (Secure + SameSite in production)
- Implemented routes: `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `GET /me`
- Admin route: `GET /admin/system-info` (ScoutAI Admin only)
- Authorization policies aligned with `docs/AUTHORIZATION_MATRIX.md`

### Operations

- `GET /health` and `GET /health/ready` (Postgres + Redis dependency checks)
- Worker `system.smoke` job proving BullMQ pipeline
- Structured logging with `requestId`
- Audit event foundation for auth/authz

### Provider foundations (interfaces + mocks)

- `packages/ai` — mock AI provider; no production LLM calls
- `packages/live` — `LiveProvider` interface + `ExternalLinkAdapter`
- `packages/video` — types and stubs only; no upload/processing

### Infrastructure and CI

- `docker-compose.yml` for **Postgres + Redis only**
- Apps run on host via `pnpm dev` (not containerized in Stage 3)
- GitHub Actions: lint, typecheck, unit tests, integration tests, build

### Documentation (source of truth)

| Document | Purpose |
| --- | --- |
| `PRODUCT_CONSTITUTION.md` | Product identity and non-negotiables |
| `ARCHITECTURE.md` | Topology and Stage 3 scope |
| `AUTHORIZATION_MATRIX.md` | Role × action matrix |
| `SECURITY.md` | Auth, CSRF, secrets, audit, rate limits |
| `PRIVACY_MODEL.md` | Privacy architecture principles |
| `AI_POLICY.md` | AI usage boundaries |
| `LIVE_ARCHITECTURE.md` | Live Foundation + provider adapters |
| `VIDEO_ARCHITECTURE.md` | Future video pipeline boundaries |
| `TESTING.md` | Test strategy and required cases |
| `DEPLOYMENT.md` | Local docker + CI + prod placeholder |
| `DEVELOPMENT.md` | Setup, ports, seed credentials |
| `PROJECT_MANIFEST.md` | Status tracker (Stage 3 verified locally) |
| `adr/ADR-001` … `ADR-006` | Architecture decisions |

## What NOT to Rebuild

Stage 4 must **extend** Stage 3, not replace it. Do **not**:

1. **Change topology** — remain modular monolith (web + api + worker); no microservices or Kubernetes.
2. **Replace PostgreSQL** — no MongoDB, Firebase, or Supabase as system of record.
3. **Reimplement auth from scratch** — use existing session + Argon2 stack in `packages/auth` and `apps/api`.
4. **Move authorization to the client** — all new routes need server policies.
5. **Import vendor SDKs in domain code** — use `packages/ai`, `packages/live`, `packages/video` adapters.
6. **Collapse packages** — maintain boundaries; add athlete domain in new modules/packages as needed.
7. **Delete or bypass audit logging** for security-relevant actions.
8. **Expose Prisma models directly as public API DTOs** — use contracts/validation package.
9. **Fake Stage 3 verification** — update `PROJECT_MANIFEST.md` only after tests pass in CI.
10. **Implement full video upload/transcode or native streaming** — out of Stage 4 scope unless explicitly replanned.

If a Stage 3 decision blocks Stage 4, write a new ADR and update the manifest — do not silently drift.

## Stage 4 — Athlete Platform Foundation (Next)

Stage 4 builds the first real athlete-facing domain on top of Stage 3.

### Recommended scope

| Area | Stage 4 intent |
| --- | --- |
| **Athlete profile** | CRUD for athlete-owned profile fields; public vs restricted field separation per `PRIVACY_MODEL.md` |
| **Guardian linking** | Invitation/approval flow; guardian read access to linked minor restricted fields |
| **Org + roster basics** | Coach/Org Admin can manage roster membership within org boundary |
| **Profile visibility** | Enforce visibility tiers on read APIs; entitlement hooks per ADR-004 |
| **Recruiter read (limited)** | Entitled recruiters view public profile fields only; no private notes UI yet unless scoped |
| **Web UI** | Athlete dashboard shell, profile edit, guardian management — minimal but real |
| **Tests** | Integration tests for new routes; extend authorization matrix coverage |

### Explicitly defer to later stages

- Native live streaming and video upload pipeline
- Production Stripe billing and paid entitlements
- Live AI scouting and search
- Recruiter verification workflow (admin UI)
- Recruiter private notes feature (schema may exist; full UI later)
- Data export / deletion self-service
- E2E Playwright suite (nice-to-have in Stage 4, not blocker if integration tests cover routes)

### Implementation sequence (suggested)

1. Read `PROJECT_MANIFEST.md` — confirm Stage 3 verification status and known issues.
2. Add domain modules to `apps/api` (e.g., `athlete`, `guardian`, `organization`) using NestJS module pattern.
3. Extend Prisma schema with athlete profile tables; migration + seed updates.
4. Implement policies before controllers (TDD against `AUTHORIZATION_MATRIX.md` **Future** rows now becoming real).
5. Add API contracts in `packages/contracts` with Zod validation.
6. Build `apps/web` pages consuming new endpoints via server actions or typed fetch.
7. Extend `pnpm test:integration` and update manifest.

## Key Files to Inspect First

```text
apps/api/src/                    # Auth modules, health, admin
apps/api/test/integration/       # Stage 3 test patterns
packages/database/prisma/        # Schema and migrations
packages/auth/                   # Session + password
packages/contracts/              # Shared DTOs (extend here)
prisma/seed.ts                   # Seed users and future fixtures
docs/AUTHORIZATION_MATRIX.md     # Add rows as you implement
turbo.json / pnpm-workspace.yaml # Workspace config
.github/workflows/ci.yml         # CI expectations
```

## Seed Accounts for Stage 4 Development

Use fictional seed users from `DEVELOPMENT.md`:

- `athlete1@scoutai.dev` / `Athlete1!`
- `guardian1@scoutai.dev` / `Guardian1!`
- `recruiter1@scoutai.dev` / `Recruiter1!`
- `coach1@scoutai.dev` / `Coach1!`
- `orgadmin1@scoutai.dev` / `OrgAdmin1!`
- `admin@scoutai.dev` / `Admin1!Scout`

## Success Criteria for Stage 4 Handoff

Stage 4 is complete when:

1. Athlete can create/edit own profile with visibility-enforced reads.
2. Guardian link workflow works for seed fixtures.
3. Coach/Org Admin roster operations respect org boundaries.
4. Authorization matrix updated; no **Future** labels on implemented actions.
5. Integration tests cover new routes; CI green.
6. `PROJECT_MANIFEST.md` updated with Stage 4 status and handoff notes for Stage 5.

## Questions and Conflicts

If code and docs disagree, **docs win until explicitly reconciled**. Update ADR + manifest when changing an accepted decision.

Legal/compliance questions (minor consent, public profile legality) — flag in manifest risks; do not invent legal conclusions.

---

*End of Stage 3 handoff. Begin Stage 4 by reading `PROJECT_MANIFEST.md` and `PRODUCT_CONSTITUTION.md`.*
