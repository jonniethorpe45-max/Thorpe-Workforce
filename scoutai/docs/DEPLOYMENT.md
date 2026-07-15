# ScoutAI Deployment

**Stage 3 foundation.** Deployment model for local development, CI, and production recommendations. Stage 3 intentionally avoids Kubernetes and multi-service production orchestration.

## Deployment Topology (Stage 3)

```text
Developer machine / CI runner
├── docker compose          → PostgreSQL, Redis only
├── apps/web (Next.js)      → port 3000, host process
├── apps/api (NestJS)       → port 4000, host process
└── apps/worker (BullMQ)    → host process, shares Redis with API
```

**Infrastructure in Docker:** Postgres + Redis  
**Application processes:** Run on host (or CI runner) via pnpm in Stage 3

This split keeps hot-reload fast during development and matches the modular monolith decision (ADR-001).

## Local Development

### Docker Compose (data layer)

```bash
docker compose up -d
```

Default services (see `docker-compose.yml`):

| Service | Image | Host port | Purpose |
| --- | --- | --- | --- |
| `postgres` | `postgres:16-alpine` | `5432` | System of record |
| `redis` | `redis:7-alpine` | `6379` | BullMQ + rate limit / session support |

Volumes persist data between restarts. Reset with `docker compose down -v` (destroys local data).

### Application processes

```bash
pnpm install
pnpm db:migrate
pnpm db:seed
pnpm dev          # Turbo: web + api + worker concurrently
```

Or individually:

```bash
pnpm --filter @scoutai/web dev
pnpm --filter @scoutai/api dev
pnpm --filter @scoutai/worker dev
```

See `DEVELOPMENT.md` for ports and environment variables.

## Environment Configuration

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `SESSION_SECRET` | Yes | Session signing / encryption secret |
| `NODE_ENV` | Yes | `development`, `test`, `production` |
| `API_URL` | Web | Internal API base for server components / proxy |
| `NEXT_PUBLIC_API_URL` | Web | Browser-accessible API URL |
| `PORT` | API | Default `4000` |
| `CORS_ORIGIN` | API | Web origin for CORS (e.g., `http://localhost:3000`) |

Copy `.env.example` to `.env` at repo root; apps load via `packages/config` or dotenv-safe.

**Production:** inject secrets via platform secret manager; never commit `.env`.

## Database Migrations

| Environment | Command |
| --- | --- |
| Local / CI | `pnpm db:migrate` (`prisma migrate deploy`) |
| Generate migration (dev) | `pnpm db:migrate:dev` |
| Seed | `pnpm db:seed` |

Production deploy pipeline must run migrations before starting new API/worker revisions.

## CI — GitHub Actions

Stage 3 CI workflow responsibilities:

```yaml
# Illustrative — see .github/workflows/ci.yml for authoritative config
jobs:
  ci:
    services:
      postgres: ...
      redis: ...
    steps:
      - checkout
      - pnpm install --frozen-lockfile
      - pnpm db:migrate
      - pnpm check           # lint + typecheck + unit tests
      - pnpm test:integration
      - pnpm build
```

Triggers: pull request and push to `main`.

Artifacts: build outputs may be cached; Docker images for apps are **not** required in Stage 3.

## Production Recommendations (Placeholder)

> **Not implemented in Stage 3.** The following is guidance for a future production cutover. No Kubernetes manifests are maintained in this repository stage.

### Recommended platform pattern

| Component | Suggestion |
| --- | --- |
| **Web** | Vercel, Netlify, or container on Fly.io / Railway / AWS App Runner |
| **API** | Single container or VM process behind HTTPS load balancer |
| **Worker** | Separate container/process (same image as API, different entrypoint) |
| **PostgreSQL** | Managed RDS, Cloud SQL, or Neon |
| **Redis** | Managed ElastiCache, Upstash, or Redis Cloud |
| **Object storage** | S3-compatible (**Future** for video) |

### Process model

```text
Internet
   │
   ▼
[CDN / Edge] ──▶ apps/web (static + SSR)
   │
   ▼
[Load balancer] ──▶ apps/api (N instances)
                         │
                         ├── PostgreSQL (managed)
                         └── Redis (managed)
apps/worker (M instances) ──▶ Redis queues
```

- Scale API and worker independently based on CPU and queue depth.
- Run at least two API instances for availability before launch.
- Worker concurrency tuned per BullMQ queue.

### Security checklist (pre-launch)

- [ ] TLS everywhere; `Secure` cookies enforced
- [ ] Secrets in platform secret manager
- [ ] Database and Redis not publicly accessible
- [ ] Automated backups and restore drill
- [ ] Rate limiting enabled
- [ ] Log aggregation without PII/secrets

### What Stage 3 explicitly excludes

- Kubernetes / Helm charts
- Terraform / Pulumi modules
- Multi-region failover
- Blue-green deployment automation

Document chosen production vendor and runbooks in `PROJECT_MANIFEST.md` when Stage 4+ approaches launch.

## Health Checks for Orchestrators

| Endpoint | Use |
| --- | --- |
| `GET /health` | Liveness — process up |
| `GET /ready` | Readiness — DB + Redis reachable |

Configure load balancer to remove instances failing `/ready` for 30+ seconds.

## Related Documents

- `DEVELOPMENT.md` — local setup
- `TESTING.md` — CI test requirements
- `SECURITY.md` — production security controls
- `adr/ADR-001-modular-monolith.md`
