# ADR-002: PostgreSQL as System of Record

**Status:** Accepted  
**Date:** 2026-07-15  
**Deciders:** ScoutAI architecture (Stage 3 foundation)

## Context

ScoutAI stores relational domain data: users, roles, guardian links, organizations, athletes, games, entitlements, audit events, and future recruiting artifacts. Data integrity, transactional consistency, and ad hoc reporting are critical for a recruiting platform handling minor athlete information.

Alternatives considered:

1. **PostgreSQL** — relational, ACID, mature ecosystem, Prisma support.
2. **MongoDB** — flexible documents; weaker default consistency for cross-entity invariants.
3. **Firebase/Firestore** — rapid prototyping; vendor coupling, limited relational modeling.
4. **Supabase** — Postgres-backed but bundled auth/realtime opinions conflicting with custom auth requirements.
5. **Polyglot persistence** — Postgres + Elasticsearch + separate graph DB (premature).

`PRODUCT_CONSTITUTION.md` mandates PostgreSQL as system of record and prohibits Firebase/MongoDB/Supabase as core architecture.

## Decision

Use **PostgreSQL** as the sole **system of record** for all durable ScoutAI domain and transactional data.

- ORM/access layer: **Prisma** in `packages/database`.
- Migrations: Prisma Migrate, applied via `pnpm db:migrate` in dev/CI/production.
- **Redis** is used for queues (BullMQ), rate limiting, and optional session cache — not as primary data store.
- Full-text search and analytics may add read-optimized stores later via explicit ADR; PostgreSQL remains authoritative.

## Consequences

### Positive

- Strong consistency for guardian links, entitlements, and financial records (future).
- Rich querying for recruiting filters (graduation year, position, geography).
- Prisma generates type-safe client; fits TypeScript monorepo.
- Managed Postgres offerings (RDS, Neon, Cloud SQL) simplify production ops.

### Negative

- Schema migrations require discipline; long-running migrations need planning at scale.
- Document-heavy media metadata still lives in Postgres rows; large binaries go to object storage (future).
- Horizontal write scaling limited compared to some NoSQL systems (acceptable for projected early load).

### Neutral / follow-up

- Read replicas and connection pooling (PgBouncer) added when monitoring indicates need.
- Audit log table growth managed via partitioning or archival policy (future).

## Related

- `docs/ARCHITECTURE.md`
- `docs/SECURITY.md` — audit logging in Postgres
- `adr/ADR-001-modular-monolith.md`
