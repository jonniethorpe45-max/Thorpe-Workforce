# ADR-004: Entitlement-Based Feature Access

**Status:** Accepted  
**Date:** 2026-07-15  
**Deciders:** ScoutAI architecture (Stage 3 foundation)

## Context

ScoutAI serves multiple roles (athlete, guardian, recruiter, coach, org admin) with overlapping but distinct access needs. Role-based access control (RBAC) alone is insufficient:

- Two recruiters may have different subscription tiers.
- A coach sees org roster data; a recruiter sees only entitled athletes.
- Live capabilities (`embed` vs `archive` vs `ai_analysis`) vary by game, org, and provider.
- Minor athlete contact info requires relationship and consent beyond a single role check.

Hard-coding `if (role === 'RECRUITER')` in controllers does not scale and risks privacy violations.

## Decision

Implement **entitlement-based feature access** as a first-class layer above RBAC:

1. **Roles** answer: *who is this user?* (Athlete, Guardian, Recruiter, Coach, Org Admin, ScoutAI Admin).
2. **Entitlements** answer: *what may this user do on this resource?* (capabilities, tiers, org scope, verification status).
3. **`EntitlementService`** (or equivalent in `packages/auth`) evaluates `viewer × resource × action` before handlers execute.
4. **Capabilities** are enumerated strings shared across live, video, and profile domains (see `LIVE_ARCHITECTURE.md`).
5. **Billing linkage (future)** — Stripe subscription state maps to entitlement grants; Stage 3 defines hooks only.
6. **Deny by default** — missing entitlement yields `403 Forbidden` and audit `authz.denied`.

RBAC remains for coarse routes (e.g., `/admin/*` requires `SCOUTAI_ADMIN`). Fine-grained reads/writes use entitlements.

## Consequences

### Positive

- Recruiter verification and paid tiers enforceable without role proliferation.
- Guardian/minor restrictions composable with org and recruiter rules.
- Live and video capabilities unified under one evaluation model.
- Authorization matrix "Restricted" cells map directly to entitlement checks.

### Negative

- More complex than pure RBAC; requires caching strategy for hot paths (Redis entitlement cache, future).
- Entitlement data model and admin UI needed before full recruiter product launch.
- Testing matrix grows; integration tests must cover entitlement permutations.

### Neutral / follow-up

- Stage 3 implements entitlement types and service skeleton; full enforcement arrives with athlete profiles (Stage 4+).
- Document new entitlements in `AUTHORIZATION_MATRIX.md` when added.

## Related

- `docs/AUTHORIZATION_MATRIX.md`
- `docs/PRIVACY_MODEL.md` — restricted contact info
- `adr/ADR-003-provider-agnostic-live.md`
