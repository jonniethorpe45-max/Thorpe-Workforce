# ScoutAI Video Architecture

**Future-facing foundation.** Stage 3 establishes architectural boundaries and package placeholders for video; **no advanced video processing ships in Stage 3**.

## Scope Boundary

| In Stage 3 | Deferred |
| --- | --- |
| `packages/video` provider interface | Direct-to-storage upload endpoints |
| Documentation and entitlement hooks | Transcoding, thumbnails, HLS packaging |
| Security requirements in `SECURITY.md` | Malware scan, content moderation |
| Worker job stubs (if any) | Production ffmpeg pipelines |

Live game viewing in MVP uses **external links** via `packages/live` (see `LIVE_ARCHITECTURE.md`). This document covers **owned media** (highlights, uploads, archives) when ScoutAI hosts or processes files.

## Design Principles

### 1. Direct-to-storage upload (Future)

Upload flow avoids proxying large binaries through `apps/api`:

```text
Client                    API                     Object Storage
  │                        │                           │
  │── POST /media/init ───▶│  authz + create MediaAsset │
  │◀─ signed PUT URL ──────│                           │
  │── PUT (binary) ────────────────────────────────────▶│
  │── POST /media/complete ▶│  enqueue process job     │
  │                        │──────────▶ Worker queue   │
```

- Signed URLs are short-lived, single-object, content-type constrained.
- `MediaAsset` row created in `pending_upload` state before client uploads.
- Completion webhook or client callback transitions to `uploaded` and enqueues processing.

### 2. Media is untrusted

All user- and org-supplied media is **untrusted input**:

| Threat | Mitigation |
| --- | --- |
| Malware | Async scan before publish (**Future**) |
| Polyglot files | Magic-byte sniffing; reject mismatched extensions |
| Oversized files | Limits at init and storage gateway |
| SSRF via URL fetch | URL allowlist for import jobs; no arbitrary fetch (**Future**) |
| XSS via metadata | Sanitize titles/descriptions; no HTML in filenames |

Workers process media in isolated jobs with resource limits. API never executes ffmpeg on uploaded content.

### 3. Provider abstraction

`packages/video` defines `VideoStorageProvider` and `VideoProcessingProvider`:

```text
apps/api / apps/worker
        │
        ▼
  packages/video
        ├── StorageProvider (S3-compatible, GCS, R2 — Future)
        ├── ProcessingProvider (transcode, thumb, clip — Future)
        └── VideoAssetRepository (Prisma-backed metadata)
```

Vendor SDKs are confined to adapter implementations. Domain code references `MediaAssetId`, statuses, and capability flags only.

### 4. Async processing

State machine for `MediaAsset`:

```text
pending_upload → uploaded → processing → ready
                    │            │
                    └────────────┴──▶ failed (retry / dead-letter)
```

| Stage | Owner | Output |
| --- | --- | --- |
| `uploaded` | API | Validates size/checksum, enqueues job |
| `processing` | Worker | Transcode, thumbnail, duration, codec metadata |
| `ready` | Worker | Updates `playbackUrl`, `thumbnailUrl`, clears temp objects |
| `failed` | Worker | Records error code; notifies uploader (**Future**) |

BullMQ queues (`video.process`, `video.clip`, etc.) with idempotent job IDs keyed by `mediaAssetId`.

### 5. Permissions

Media access mirrors game/profile entitlements (ADR-004):

| Action | Policy |
| --- | --- |
| Init upload | Authenticated; scoped to user/org/athlete profile |
| View playback URL | Entitlement check; URLs are signed and time-limited |
| Delete | Owner, org admin, or ScoutAI admin per retention policy |
| Clip creation | Requires `clipping` capability on parent game or asset |

Playback URLs must not be long-lived public S3 paths. Use CDN signed cookies or short TTL signed URLs.

## Relationship to Live Architecture

| Concern | Live (`packages/live`) | Video (`packages/video`) |
| --- | --- | --- |
| Primary use | Game broadcast link/embed | Hosted highlights, uploads, archives |
| Stage 3 | ExternalLink adapter | Interface + docs only |
| Processing | None (provider hosts video) | Worker transcode pipeline (Future) |
| AI analysis | Entitlement flag on live session | Entitlement on `MediaAsset` (Future) |

Native live streaming (recorded to archive) bridges both: live ingest ends in `MediaAsset` processed by `packages/video`.

## Data Model (Foundation)

Future Prisma models (names illustrative):

- `MediaAsset` — type, status, owner, org, storage key, duration, capabilities granted
- `MediaVariant` — renditions (1080p, 720p, thumb)
- `Clip` — start/end offsets, parent asset, creator

Stage 3 may include migration stubs without full API surface.

## Observability

Worker jobs emit structured logs: `mediaAssetId`, `jobId`, `stage`, `durationMs`, `provider`. No signed URLs or storage secrets in logs.

## Stage 3 Checklist

- [ ] `packages/video` exported types and no-op/mock providers
- [ ] Entitlement enum includes video-related capabilities (shared with live)
- [ ] SECURITY.md upload boundary documented
- [ ] No production upload routes exposed

## Related Documents

- `LIVE_ARCHITECTURE.md`
- `SECURITY.md` — upload security boundary
- `adr/ADR-003-provider-agnostic-live.md`
- `adr/ADR-004-entitlement-based-feature-access.md`
