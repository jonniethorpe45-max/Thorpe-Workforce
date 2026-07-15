# ScoutAI AI Policy

**Stage 3 foundation.** This policy governs how ScoutAI uses artificial intelligence across recruiting intelligence features. It applies to `packages/ai`, worker jobs, and any API route that invokes an AI provider.

## Core Principle

**AI assists decisions; it does not verify facts.**

Humans, primary sources, and explicitly **verified** data records are the authority for factual claims about athletes, performance, and recruiting status. AI-generated content is advisory, probabilistic, and must never be presented as ground truth without independent verification.

## Responsibilities

| Actor | Responsibility |
| --- | --- |
| Product / UX | Label AI outputs; provide paths to source data |
| Engineering | Enforce structured outputs, validation, and access boundaries |
| Operators | Monitor provider usage, cost, and failure modes |
| Legal / Compliance | Review copy and data processing agreements (**before production**) |

## Observation vs Verified Data

ScoutAI distinguishes two data provenance classes in the domain model and UI:

| Class | Definition | Examples | UI treatment |
| --- | --- | --- | --- |
| **Observation** | Machine-inferred, user-reported, or AI-derived; not independently verified | AI scouting blurb, crowd-sourced stat, model-estimated fit score | Badge: "AI suggestion" / "Unverified" |
| **Verified** | Confirmed by trusted process (official feed, admin verification, primary document) | Coach-submitted official stats, verified combine result, admin-approved recruiter status | Badge: "Verified" with source link |

**Rules:**

1. AI outputs are always **Observation** unless a separate human verification workflow promotes them (**Future**).
2. Downstream features (search ranking, recruiter alerts) may weight verified data higher than observations.
3. Never auto-promote AI output to verified status without explicit workflow and audit event.

## No Unrestricted Database Access

AI components **must not** receive arbitrary SQL, ORM escape hatches, or full database dumps.

| Allowed | Prohibited |
| --- | --- |
| Purpose-built read services returning scoped DTOs | Raw `prisma.$queryRaw` from AI tool handlers |
| Parameterized queries behind repository methods | "Run any query" agent tools |
| Redacted context windows sized to task | Exporting full athlete tables to prompts |

Worker and API code assemble **minimal context** for each AI call: only fields required for the task, respecting authorization of the initiating user.

## Provider Abstraction

AI providers are integrated exclusively through `packages/ai`:

```text
apps/api / apps/worker
        │
        ▼
  packages/ai  ──▶  AiProvider interface
        │                │
        │                ├── MockAiProvider (Stage 3 default)
        │                ├── OpenAiCompatibleProvider (Future)
        │                └── AnthropicProvider (Future)
        ▼
  Structured task functions (summarize, tag, rank)
```

- Application code calls task-level functions (e.g., `generateScoutingSummary`), not vendor SDKs directly.
- Provider selection is configuration-driven per environment.
- API keys live server-side only; never in `apps/web` bundles.

See `adr/ADR-005-ai-provider-abstraction.md`.

## Structured Output Validation

All AI responses used programmatically must:

1. Request **JSON or schema-constrained** output from the provider.
2. Validate against a **Zod** (or equivalent) schema before persistence or API return.
3. Reject or safely degrade on validation failure (log `ai.output.invalid`, return user-safe error, do not persist garbage).

Free-text AI responses shown directly to users must still pass content length limits and profanity/safety filters where appropriate (**Future** moderation layer).

## Output Labeling

Any user-visible AI-generated content must include:

- Clear label (e.g., "AI-generated", "ScoutAI Insight").
- Timestamp of generation.
- Optional link to inputs used (when not exposing restricted data).

Labels are required in API response metadata (`source: "ai"`, `provenance: "observation"`) so front-end and future clients render consistently.

## Prohibited Uses (without explicit ADR + legal review)

- Automated final recruiting decisions presented as binding offers or scholarships.
- Generating contact info or personal data not already in authorized context.
- Impersonating athletes, coaches, or recruiters in outbound communications.
- Facial recognition or biometric identification from video (**not planned**).
- Training on user data via provider opt-in without documented consent and DPA.

## Logging and Retention

- Log AI task name, provider, latency, token usage (aggregated), and `requestId`.
- Do **not** log full prompts or completions containing PII in production; use truncated hashes or debug-flagged dev-only logs.
- Retain AI interaction metadata per privacy retention policy (**Future**).

## Stage 3 Scope

Stage 3 delivers:

- `packages/ai` interface and mock provider
- Schema types for AI metadata on future entities
- Policy documentation (this file)

Stage 3 does **not** ship production AI features, live LLM calls in user flows, or AI-powered search.

## Related Documents

- `PRIVACY_MODEL.md` — minor data and collection limits
- `SECURITY.md` — secrets and logging
- `adr/ADR-005-ai-provider-abstraction.md`
- `LIVE_ARCHITECTURE.md` — AI analysis as a separate live capability entitlement
