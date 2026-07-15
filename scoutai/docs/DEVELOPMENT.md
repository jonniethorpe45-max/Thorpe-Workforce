# ScoutAI Development Guide

**Stage 3 foundation.** Setup instructions for contributors building the ScoutAI modular monolith locally.

## Prerequisites

| Tool | Version |
| --- | --- |
| Node.js | 20 LTS or newer |
| pnpm | 9.x (see `packageManager` in root `package.json`) |
| Docker + Docker Compose | For PostgreSQL and Redis |
| Git | Latest stable |

Optional: [direnv](https://direnv.net/) for automatic `.env` loading.

## Repository Layout

```text
ScoutAI/
├── apps/
│   ├── web/          Next.js App Router
│   ├── api/          NestJS HTTP API
│   └── worker/       BullMQ job processors
├── packages/
│   ├── database/     Prisma schema + client
│   ├── auth/         Session + password utilities
│   ├── config/       Environment validation
│   ├── ai/           AI provider abstraction (mock in Stage 3)
│   ├── live/         Live provider adapters
│   ├── video/        Video provider stubs (Stage 3)
│   └── …             contracts, ui, testing helpers
├── prisma/           Migrations + seed
├── docs/             Architecture and policy docs
├── docker-compose.yml
├── turbo.json
└── pnpm-workspace.yaml
```

## First-Time Setup

```bash
# Clone and enter repository
git clone <repo-url> ScoutAI
cd ScoutAI

# Install dependencies
pnpm install

# Environment
cp .env.example .env
# Edit .env if your Docker ports differ from defaults

# Start data services
docker compose up -d

# Wait for Postgres readiness, then migrate and seed
pnpm db:migrate
pnpm db:seed

# Start all apps in development mode
pnpm dev
```

## Ports

| Service | URL / Port |
| --- | --- |
| Web (`apps/web`) | http://localhost:3000 |
| API (`apps/api`) | http://localhost:4000 |
| API health | http://localhost:4000/health |
| API ready | http://localhost:4000/ready |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |

The web app proxies or calls the API via `NEXT_PUBLIC_API_URL` (default `http://localhost:4000`).

## Seed Credentials

> **Fictional accounts only.** These emails and personas are synthetic test data. They do **not** represent real people and must **not** be used to represent real minors. Do not send email to `@scoutai.dev` domains.

After `pnpm db:seed`, the following accounts are available in local and CI test databases:

| Role | Email | Password | Notes |
| --- | --- | --- | --- |
| ScoutAI Admin | `admin@scoutai.dev` | `AdminPass1!` | Access to `/admin/system-info` |
| Athlete | `athlete@scoutai.dev` | `AthletePass1!` | Sample high school athlete |
| Recruiter | `recruiter@scoutai.dev` | `RecruiterPass1!` | Unverified recruiter baseline |

All seed passwords meet minimum length and complexity rules enforced by registration validation.

**Re-seed:** `pnpm db:seed` (idempotent upsert). **Full reset:** `pnpm db:reset` (drops data, migrates, seeds) if implemented; otherwise `docker compose down -v && docker compose up -d && pnpm db:migrate && pnpm db:seed`.

## Common Commands

| Command | Description |
| --- | --- |
| `pnpm dev` | Start web + api + worker via Turborepo |
| `pnpm build` | Production build all packages/apps |
| `pnpm check` | Lint + typecheck + unit tests |
| `pnpm test` | Unit tests |
| `pnpm test:integration` | API integration tests (DB + Redis required) |
| `pnpm lint` | ESLint across workspace |
| `pnpm typecheck` | TypeScript validation |
| `pnpm db:migrate` | Apply Prisma migrations |
| `pnpm db:migrate:dev` | Create migration in development |
| `pnpm db:seed` | Run seed script |
| `pnpm db:studio` | Open Prisma Studio |

### Filtered commands

```bash
pnpm --filter @scoutai/api dev
pnpm --filter @scoutai/web dev
pnpm --filter @scoutai/worker dev
```

## Environment Variables

See `.env.example` for the full list. Minimum for local dev:

```env
DATABASE_URL="postgresql://scoutai:scoutai@localhost:5432/scoutai"
REDIS_URL="redis://localhost:6379"
SESSION_SECRET="dev-only-change-in-production-min-32-chars"
NODE_ENV="development"
NEXT_PUBLIC_API_URL="http://localhost:4000"
CORS_ORIGIN="http://localhost:3000"
```

## Verifying Setup

```bash
# API health (no auth)
curl -s http://localhost:4000/health | jq

# Login and call /me
curl -s -c cookies.txt -X POST http://localhost:4000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@scoutai.dev","password":"AdminPass1!"}'

curl -s -b cookies.txt http://localhost:4000/me | jq

# Admin route
curl -s -b cookies.txt http://localhost:4000/admin/system-info | jq
```

Integration tests in `pnpm test:integration` automate these flows.

## IDE Setup

- **TypeScript:** Use workspace version; open repo root for correct project references.
- **ESLint + Prettier:** Format on save recommended.
- **Prisma:** Install Prisma extension for schema highlighting.

## Troubleshooting

| Issue | Fix |
| --- | --- |
| `ECONNREFUSED` on migrate | Ensure `docker compose up -d` and Postgres healthy |
| Port 3000 in use | Stop other Next.js apps or set `PORT` for web |
| Stale sessions | Clear browser cookies for localhost |
| Prisma client out of date | `pnpm --filter @scoutai/database generate` |
| Redis connection errors | Check `REDIS_URL` matches docker-compose port |

## Documentation Hierarchy

Read before implementing features:

1. `docs/PRODUCT_CONSTITUTION.md`
2. `docs/ARCHITECTURE.md`
3. `docs/PROJECT_MANIFEST.md`
4. Domain docs (`SECURITY.md`, `AUTHORIZATION_MATRIX.md`, etc.)

## Related Documents

- `DEPLOYMENT.md` — Docker and CI
- `TESTING.md` — test commands and required cases
- `AI_HANDOFF.md` — Stage 4 builder instructions
