# ScoutAI Live Architecture

**Stage 3 foundation.** This document defines how ScoutAI models live games, external video providers, and capability-based rights. Native streaming is future work; Stage 3 establishes contracts and the initial adapter only.

## Design Goals

1. **Game intelligence belongs to ScoutAI** — schedules, teams, scores, play metadata, and recruiting context live in PostgreSQL as the system of record.
2. **Video providers are adapters** — YouTube, Hudl, Vimeo, school CDN links, and future native streams all implement the same interface.
3. **Rights are capability-based** — link, embed, archive, clipping, and AI analysis are separate entitlements tied to provider contracts and org settings.
4. **MVP uses Live Foundation** — external links and embeds before investing in ingest/transcode infrastructure.

## Conceptual Model

```text
┌─────────────────────────────────────────────────────────┐
│                    ScoutAI Domain                        │
│  Game, Team, Venue, LiveSession, LiveSource, Entitlement │
└───────────────────────────┬─────────────────────────────┘
                            │ owns metadata & rights
                            ▼
              ┌─────────────────────────────┐
              │   LiveProvider (interface)   │
              │   packages/live              │
              └─────────────┬───────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
 ExternalLinkAdapter   HudlAdapter (*)   NativeStreamAdapter (*)
   (Stage 3)            (Future)            (Future)

(*) Provider adapters implemented when contracts and legal review complete.
```

A **LiveSession** represents a point-in-time broadcast or replay window for a **Game**. A **LiveSource** binds a session to a provider-specific reference (URL, embed ID, stream key metadata).

## Live Foundation (MVP)

Stage 3 and early product stages ship **Live Foundation**:

| Capability | MVP behavior |
| --- | --- |
| Game record | ScoutAI stores game metadata (teams, time, location, status) |
| External link | Coach/org admin attaches HTTPS URL to approved providers |
| Embed preview | Front-end renders provider embed when `embed` entitlement allows |
| Live status | Manual or webhook-driven status updates (**Future** automation) |
| Archive link | Pointer to post-game replay URL; no ScoutAI-hosted archive in MVP |

ScoutAI does **not** re-host provider video in MVP. Intelligence (stats, highlights metadata, recruiting notes) attaches to the game entity regardless of video source.

## Provider Adapter Interface

All providers implement `LiveProvider` in `packages/live`:

```typescript
// Illustrative — see packages/live for authoritative types
interface LiveProvider {
  readonly providerId: string;
  resolveSource(ref: ProviderRef): Promise<ResolvedSource>;
  getEmbedConfig(resolved: ResolvedSource): EmbedConfig | null;
  validateUrl(url: string): ValidationResult;
  supportedCapabilities(): LiveCapability[];
}
```

`ResolvedSource` contains normalized fields: `title`, `thumbnailUrl`, `embedHtml` or `embedUrl`, `expiresAt`, `providerRaw` (internal only).

## Initial Adapter: ExternalLink

**ExternalLinkAdapter** (Stage 3) supports:

- Validated HTTPS URLs to known patterns (YouTube, Vimeo, generic oEmbed-capable hosts where configured).
- `link` capability always (open in new tab).
- `embed` capability when oEmbed or provider rules allow and org entitlement permits.
- No archive ingestion, clipping, or AI analysis at adapter level in Stage 3.

Unknown URLs may be stored as opaque links with `embed` disabled pending admin allowlist expansion.

## Future: Native Streaming

**NativeStreamAdapter** will implement the same `LiveProvider` interface:

| Aspect | Native stream |
| --- | --- |
| Ingest | RTMP/SRT/WebRTC to managed ingress (**Future**) |
| Playback | HLS/DASH via CDN |
| Archive | Recorded to object storage; `archive` capability |
| Clipping | Worker-generated clips; `clipping` capability |
| AI analysis | Frame/event pipeline; `ai_analysis` capability |

Switching from ExternalLink to native stream for a game updates the `LiveSource` record; game intelligence and entitlements remain attached to the game, not the provider.

## Capability-Based Rights

Capabilities are enumerated and enforced server-side:

| Capability | Description | Typical grantee |
| --- | --- | --- |
| `link` | Open external URL | Public / entitled viewers |
| `embed` | Inline player on ScoutAI | Entitled viewers; subject to provider ToS |
| `archive` | Access replay after live ends | Org members, recruiters with entitlement |
| `clipping` | Create/share clips | Coaches, org admins |
| `ai_analysis` | Run AI on video content | Paid tier / org entitlement (**Future**) |

Entitlements are evaluated per **viewer × game × capability** (see ADR-004). Provider adapters advertise which capabilities they can support; org/game settings enable subsets.

```text
Viewer request: GET /games/:id/live
       │
       ▼
 Authorization + EntitlementService
       │
       ├── game.liveSource.provider
       └── filter capabilities[] → response DTO
```

Response DTO never includes embed HTML for capabilities the viewer lacks.

## Webhooks and Status (Future)

Providers may push live start/end events via signed webhooks (**Future**). Until then, coaches mark games live/complete manually or via org integrations.

## Stage 3 Deliverables

- `packages/live` with `LiveProvider` interface and `ExternalLinkAdapter`
- Domain types for `Game`, `LiveSession`, `LiveSource` (schema foundation; minimal CRUD **Future** in Stage 4)
- Mock/fixture data for development
- Documentation (this file)

## Non-Goals (Stage 3)

- RTMP ingest, transcoding, or CDN configuration
- Real-time play-by-play AI
- Provider OAuth integrations (Hudl API, etc.)

## Related Documents

- `VIDEO_ARCHITECTURE.md` — upload and async media processing (separate from live adapters)
- `adr/ADR-003-provider-agnostic-live.md`
- `adr/ADR-004-entitlement-based-feature-access.md`
- `AUTHORIZATION_MATRIX.md`
