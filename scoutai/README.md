# ScoutAI

**Stage 3 foundation** for a sports recruiting intelligence platform (US high school football first, multi-sport later). ScoutAI helps athletes, guardians, recruiters, and coaches connect through structured profiles, video, live events, and AI-assisted insights — built as a modular monolith with clear package boundaries.

Stage 3 delivers the repository skeleton, authentication baseline, operational endpoints, background worker smoke job, and documentation — **not** the full athlete or recruiter product UI.

**Downloadable Stage 3 report:** [docs/STAGE3_COMPLETION_REPORT.md](docs/STAGE3_COMPLETION_REPORT.md)

## Architecture

```text
┌────────────┐     ┌────────────┐     ┌────────────┐
│  apps/web  │────▶│  apps/api  │────▶│ PostgreSQL │
│  Next.js   │     │  NestJS    │     └────────────┘
└────────────┘     │            │────▶ Redis / BullMQ
                   └─────┬──────┘
                         │ enqueue
                   ┌─────▼──────┐
                   │ apps/worker│
                   │  BullMQ    │
                   └────────────┘
```

| Component | Role |
| --- | --- |
| `apps/web` | Next.js App Router UI (foundation screens) |
| `apps/api` | NestJS HTTP API — auth, authorization, health |
| `apps/worker` | BullMQ job processors (`system.smoke`) |
| `packages/*` | Shared domain, auth, config, observability, adapters |
| PostgreSQL | System of record (Prisma) |
| Redis | Queue backend + readiness dependency |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for topology details and ADRs under `docs/adr/`.

## Repository structure

```text
ScoutAI/
├── apps/
│   ├── web/          # Next.js App Router (@scoutai/web)
│   ├── api/          # NestJS HTTP API (@scoutai/api)
│   └── worker/       # BullMQ worker (@scoutai/worker)
├── packages/         # Shared TypeScript packages
├── prisma/           # Migrations + seed
├── docs/             # Architecture, security, testing guides
├── infrastructure/   # Docker Compose, scripts
├── turbo.json
├── pnpm-workspace.yaml
└── .env.example
```

## Requirements

| Tool | Version |
| --- | --- |
| Node.js | 20 LTS or newer |
| pnpm | 9.x |
| Docker + Docker Compose | PostgreSQL and Redis |

## Local setup

```bash
# Install dependencies
pnpm install

# Environment (repo root)
cp .env.example .env
# Web app reads NEXT_PUBLIC_API_URL from apps/web/.env.local (default http://localhost:4000)

# Start Postgres + Redis
pnpm dev:infra
# or: docker compose up -d

# Database
pnpm db:migrate
pnpm db:seed

# Build shared packages
pnpm build

# Start all apps (web :3000, api :4000, worker)
pnpm dev
```

### Ports

| Service | URL |
| --- | --- |
| Web | http://localhost:3000 |
| API | http://localhost:4000 |
| Health | http://localhost:4000/health |
| Ready | http://localhost:4000/ready |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

## Commands

| Command | Description |
| --- | --- |
| `pnpm dev` | Start web, api, and worker in parallel |
| `pnpm dev:web` | Next.js on port 3000 |
| `pnpm dev:api` | API on port 4000 |
| `pnpm dev:worker` | BullMQ worker |
| `pnpm build` | Production build (Turborepo) |
| `pnpm typecheck` | TypeScript across workspace |
| `pnpm lint` | Lint all packages/apps |
| `pnpm test` | Unit tests |
| `pnpm test:integration` | Integration tests (DB + Redis) |
| `pnpm check` | lint + typecheck + test + integration + build |

Filtered examples:

```bash
pnpm --filter @scoutai/web dev
pnpm --filter @scoutai/worker test:integration
```

## Testing

- **Unit tests** — Vitest in `packages/*` and `apps/worker/src`
- **Integration** — API tests against real DB/Redis; worker `system.smoke` job with Redis
- **E2E** — Planned in Stage 4+ (Playwright)

```bash
pnpm test
pnpm test:integration
```

Required Stage 3 cases are listed in [docs/TESTING.md](docs/TESTING.md).

## Environment variables

Minimum for local development (see `.env.example`):

```env
DATABASE_URL=postgresql://scoutai:scoutai@127.0.0.1:5432/scoutai?schema=public
REDIS_URL=redis://127.0.0.1:6379
SESSION_SECRET=dev-only-change-me-to-a-long-random-string
NODE_ENV=development
CORS_ORIGIN=http://localhost:3000
```

Web app (`apps/web/.env.local`):

```env
NEXT_PUBLIC_API_URL=http://localhost:4000
NEXT_PUBLIC_NODE_ENV=development
```

The worker loads the root `.env` from `apps/worker` via `../../.env`.

### Cross-origin cookies (web → API)

The web app calls the API with `credentials: 'include'` so HTTP-only session cookies are sent from `http://localhost:3000` to `http://localhost:4000`. The API must:

1. Set `Access-Control-Allow-Origin` to the web origin (not `*`)
2. Set `Access-Control-Allow-Credentials: true`
3. Configure `CORS_ORIGIN=http://localhost:3000` in the API environment

See [docs/SECURITY.md](docs/SECURITY.md) for the full security model.

## Seed credentials

After `pnpm db:seed`, these fictional `@scoutai.dev` accounts are available (local/CI only):

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@scoutai.dev` | `AdminPass1!` |
| Athlete | `athlete@scoutai.dev` | `AthletePass1!` |
| Recruiter | `recruiter@scoutai.dev` | `RecruiterPass1!` |

> Do not use these accounts to represent real people. Do not send email to `@scoutai.dev`.

## Worker smoke job

The worker (`@scoutai/worker`) connects to Redis and processes the `scoutai-system` queue. Job name `system.smoke` logs structured completion and returns `{ ok: true }`.

```bash
pnpm --filter @scoutai/worker dev
pnpm --filter @scoutai/worker test:integration
```

## Web foundation pages

| Route | Purpose |
| --- | --- |
| `/` | ScoutAI foundation landing |
| `/sign-in` | Email/password login → `POST /auth/login` |
| `/register` | Registration → `POST /auth/register` |
| `/app` | Authenticated dashboard (user, roles, API health/ready) |
| `/unauthorized` | Access denied message |

API client helpers live in `apps/web/lib/api.ts`.

## Documentation

| Document | Purpose |
| --- | --- |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Contributor setup, ports, commands |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System topology and Stage 3 scope |
| [docs/TESTING.md](docs/TESTING.md) | Test pyramid and required cases |
| [docs/SECURITY.md](docs/SECURITY.md) | Auth, CORS, sessions, rate limits |
| [docs/AUTHORIZATION_MATRIX.md](docs/AUTHORIZATION_MATRIX.md) | Role × action matrix |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Docker and CI |
| [docs/AI_HANDOFF.md](docs/AI_HANDOFF.md) | Stage 4 builder handoff |
| [docs/PRODUCT_CONSTITUTION.md](docs/PRODUCT_CONSTITUTION.md) | Product non-negotiables |

## License

Private — ScoutAI Stage 3 foundation repository.
