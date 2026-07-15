# ADR-006: Multi-Sport Configurable Data Model

**Status:** Accepted  
**Date:** 2026-07-15  
**Deciders:** ScoutAI architecture (Stage 3 foundation)

## Context

ScoutAI launches with **United States high school football** but the product constitution mandates expansion to multiple sports and international markets without architectural rewrite. Sports differ in positions, statistics, season structure, and recruiting norms.

Approaches considered:

1. **Football-only schema** — fastest MVP; guaranteed migration pain for second sport.
2. **EAV (entity-attribute-value)** — maximum flexibility; poor query ergonomics and type safety.
3. **Configurable sport definitions + typed core** — sport registry drives positions/stats; shared entities (Athlete, Game, Organization) remain relational.
4. **Separate database per sport** — operational nightmare.

## Decision

Adopt a **multi-sport configurable data model**:

1. **Shared core entities** — `User`, `Athlete`, `Organization`, `Game`, `Team`, `Season` — sport-agnostic with `sportId` foreign key where applicable.
2. **Sport registry** — `Sport` table or configuration package defining code (`football`, `basketball`), display name, and enabled flag.
3. **Configurable taxonomies per sport** — positions, stat categories, and event types stored as configuration (DB tables or versioned JSON in `packages/contracts`), not hard-coded enums in application logic.
4. **Football-first seed** — Stage 3/4 migrations seed football positions and stat keys as reference configuration.
5. **API validation** — Zod schemas parameterized by sport config; reject invalid position/stat combinations at boundary.
6. **No sport-specific tables** unless performance measurement proves need (e.g., football play-by-play); prefer `GameEvent` with typed payload validated per sport schema.

Domain language in UI and docs uses sport-neutral terms ("position", "stat line") with sport-specific labels from config.

## Consequences

### Positive

- Second sport adds configuration and UI mappings, not greenfield schema.
- Recruiters searching across sports (future) use shared athlete identity model.
- International expansion adjusts config (units, season calendar) without forked codebase.
- Prisma remains viable; no EAV query complexity for common paths.

### Negative

- Higher upfront modeling cost than football-only shortcuts.
- Sport config versioning required when definitions change mid-season.
- Complex sports (soccer lineups, baseball box scores) stress generic event models — may need sport extensions later.

### Neutral / follow-up

- Stage 3 establishes `sportId` on schema stubs; full config admin UI is later stage work.
- Analytics and leaderboards read sport config for aggregation keys.
- New ADR if a sport requires dedicated storage (e.g., tracking sensor data).

## Related

- `docs/PRODUCT_CONSTITUTION.md` — expansion mandate
- `docs/ARCHITECTURE.md`
- `adr/ADR-002-postgresql-system-of-record.md`
