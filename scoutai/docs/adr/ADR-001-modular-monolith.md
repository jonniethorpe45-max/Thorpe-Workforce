# ADR-001: Modular Monolith

**Status:** Accepted  
**Date:** 2026-07-15  
**Deciders:** ScoutAI architecture (Stage 3 foundation)

## Context

ScoutAI is an early-stage sports recruiting intelligence platform targeting US high school football first, with multi-sport expansion planned. The team must ship a secure, testable foundation quickly without operational overhead that outpaces product-market fit.

Competing approaches considered:

1. **Microservices** — independent deployable services per domain (auth, athletes, live, billing).
2. **Serverless-only** — API Gateway + Lambda functions per route group.
3. **Modular monolith** — single repository with multiple apps (`web`, `api`, `worker`) and strict internal package boundaries.
4. **BaaS (Firebase/Supabase)** — outsourced auth and database.

Constraints from `PRODUCT_CONSTITUTION.md`:

- Foundation before features; avoid premature distributed-system complexity.
- TypeScript strict mode; PostgreSQL system of record.
- Clear boundaries for future extraction (live, AI, video as adapter packages).
- No Kubernetes in Stage 3.

## Decision

Adopt a **modular monolith** organized as a pnpm/Turborepo workspace:

| Deployable | Responsibility |
| --- | --- |
| `apps/web` | Next.js UI |
| `apps/api` | NestJS HTTP API, auth, authorization, domain modules |
| `apps/worker` | BullMQ background jobs |

Shared logic lives in `packages/*` with explicit dependency rules (domain packages do not import NestJS or Next.js).

Deploy as **three processes** (or two if worker shares API container image with different entrypoint) behind standard HTTPS infrastructure. Extract services from packages only when measurable scale or team boundaries require it.

## Consequences

### Positive

- Single repo simplifies refactoring, testing, and documentation alignment.
- One PostgreSQL database and migration pipeline; no distributed transaction problems in early stages.
- Fast local development: `pnpm dev` runs all apps; Docker only for Postgres and Redis.
- Package boundaries (`auth`, `ai`, `live`, `video`) preserve clean extraction seams.

### Negative

- API and worker scale together unless separately deployed from same build artifact.
- Discipline required to enforce module boundaries; violations can create a "big ball of mud" without lint rules and code review.
- Single database blast radius; mitigated by backups and eventual read replicas.

### Neutral / follow-up

- Production may run API and worker on separate containers without changing code structure.
- ADR review required before splitting any package into an external service.

## Related

- `docs/ARCHITECTURE.md`
- `adr/ADR-002-postgresql-system-of-record.md`
