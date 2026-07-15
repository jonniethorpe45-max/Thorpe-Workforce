# ScoutAI Product Constitution

## Identity

ScoutAI is a sports technology and recruiting intelligence platform.

**Mission:** Become the Global Athletic Talent Intelligence Network.

**Initial focus:** United States high school football recruiting.

**Expansion mandate:** Architecture, domain language, and data models must support future multi-sport and international expansion without rewrite.

## Guiding Principles

1. **Foundation before features.** Controlled stages. Do not collapse later product surface into early scaffolds.
2. **Correctness over volume.** Security, maintainability, testability, and documentation outrank superficial feature count.
3. **Modular monolith.** One deployable application topology (web + API + worker) with clear internal package boundaries. Extract later only when scale requires it.
4. **Provider-agnostic capabilities.** Live video, AI, billing, notifications, and storage are adapters behind contracts. Core domain never imports vendor SDKs directly.
5. **Authorization is server-side.** Front-end route hiding is never an access-control boundary.
6. **Minor athlete sensitivity.** High school athletes may be minors. Collect minimally. Prefer guardian-aware flows. Treat contact and identity data as restricted.
7. **AI assists; humans and verified data decide.** AI outputs are labeled, structured, and never treated as fact verification.
8. **Auditability.** Security-relevant actions leave append-only audit trails without logging secrets.
9. **Documentation is architecture.** Source-of-truth hierarchy (below) is binding. Silent architecture drift is forbidden.
10. **Stage discipline.** Builders implement only their stage scope. Unfinished later-stage work is documented, not faked.

## Source of Truth Hierarchy

1. `docs/PRODUCT_CONSTITUTION.md`
2. `docs/ARCHITECTURE.md`
3. `docs/PROJECT_MANIFEST.md`
4. Domain-specific docs (`SECURITY.md`, `PRIVACY_MODEL.md`, `AI_POLICY.md`, `LIVE_ARCHITECTURE.md`, `VIDEO_ARCHITECTURE.md`, ADRs, etc.)
5. Code

If code and docs disagree, resolve the conflict explicitly and record the decision in the manifest or an ADR.

## Stage Boundaries

| Stage | Intent |
| --- | --- |
| Stage 3 (this repo foundation) | Repository bootstrap, auth, authz, health, worker smoke, docs, CI |
| Stage 4+ | Athlete platform and later product surfaces |

Stage 3 does **not** include full Athlete Passport, game statistics, native streaming, production billing, AI search, or recruiter pipeline.

## Non-Negotiables

- PostgreSQL is the system of record.
- Redis supports sessions/queues/cache — not the primary database.
- TypeScript strict mode for application logic.
- No microservices or Kubernetes in Stage 3.
- No Firebase/MongoDB/Supabase as core architecture.
- No passwords, secrets, or payment credentials in logs or API responses.
