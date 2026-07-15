# ADR-003: Provider-Agnostic Live

**Status:** Accepted  
**Date:** 2026-07-15  
**Deciders:** ScoutAI architecture (Stage 3 foundation)

## Context

ScoutAI game intelligence (schedules, scores, teams, recruiting context) must remain valuable regardless of where video is hosted. Schools and organizations already use YouTube, Hudl, Vimeo, and direct CDN links. Future product stages may add ScoutAI-native streaming.

Without a provider abstraction, the domain layer would embed YouTube URLs, Hudl SDK calls, and native stream keys in controllers and UI — making provider switches expensive and entitlements impossible to model consistently.

## Decision

Model live video through a **`LiveProvider` interface** in `packages/live`:

1. **Game intelligence belongs to ScoutAI** — `Game`, `LiveSession`, and `LiveSource` entities in PostgreSQL own metadata and rights.
2. **Video providers are adapters** implementing `LiveProvider` (resolve URL, embed config, capability advertisement).
3. **MVP ships Live Foundation** — `ExternalLinkAdapter` for validated HTTPS/oEmbed links; no ScoutAI video ingest in Stage 3.
4. **Future native streaming** implements the same interface (`NativeStreamAdapter`) without changing game domain code.
5. **Capability-based rights** (`link`, `embed`, `archive`, `clipping`, `ai_analysis`) are evaluated per viewer independently of provider internals.

Application code (`apps/api`, `apps/web`) depends only on normalized DTOs from the live package, never on provider SDKs directly.

## Consequences

### Positive

- Schools can attach existing streams on day one without migration to ScoutAI CDN.
- Provider outages or ToS changes isolated to adapter layer.
- Entitlements uniform across external and native sources.
- Stage 3 can ship interface + ExternalLink with zero RTMP infrastructure cost.

### Negative

- Lowest-common-denominator features across providers (e.g., no Hudl-specific UI without adapter extensions).
- oEmbed and provider URL validation require ongoing maintenance as hosts change patterns.
- Native streaming still requires significant future investment (ingress, CDN, recording).

### Neutral / follow-up

- Provider-specific adapters (Hudl API, YouTube Data API) added when contracts and legal review complete.
- Webhooks for live status updates standardized in live package (future).

## Related

- `docs/LIVE_ARCHITECTURE.md`
- `adr/ADR-004-entitlement-based-feature-access.md`
- `adr/ADR-005-ai-provider-abstraction.md` (parallel adapter pattern)
