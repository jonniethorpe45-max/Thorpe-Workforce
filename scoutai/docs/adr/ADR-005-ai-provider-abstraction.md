# ADR-005: AI Provider Abstraction

**Status:** Accepted  
**Date:** 2026-07-15  
**Deciders:** ScoutAI architecture (Stage 3 foundation)

## Context

ScoutAI will use AI for scouting summaries, fit scoring, tagging, and future video analysis. LLM providers (OpenAI, Anthropic, open-weight hosts) differ in APIs, pricing, rate limits, and data processing terms. Vendor lock-in at the domain layer would complicate compliance review and provider migration.

Product policy (`AI_POLICY.md`) requires:

- AI assists; does not verify facts.
- No unrestricted database access for AI tools.
- Structured output validation.
- User-visible labeling of AI-generated content.

## Decision

Integrate AI exclusively through **`packages/ai`**:

1. Define **`AiProvider` interface** with task-level methods (not raw chat completions exposed to domain code).
2. Ship **`MockAiProvider`** as Stage 3 default; no production API keys required for CI.
3. Add vendor adapters (`OpenAiCompatibleProvider`, etc.) behind configuration flags when approved.
4. All programmatic outputs pass **Zod schema validation** before persistence or API return.
5. API keys and provider SDK imports exist **only** inside `packages/ai` adapter files.
6. AI metadata (`source: "ai"`, `provenance: "observation"`) attached to responses per `AI_POLICY.md`.

`apps/api` and `apps/worker` call `packages/ai` functions; they do not import `@anthropic-ai/sdk` or `openai` directly.

## Consequences

### Positive

- Provider swap or multi-provider routing without touching athlete/recruiter modules.
- Mock provider enables deterministic tests and offline development.
- Centralized logging, rate limiting, and cost accounting for AI calls.
- Aligns with privacy review: prompts assembled in one place with redaction rules.

### Negative

- Thin wrapper risk if task APIs leak provider-specific concepts — task design must stay vendor-neutral.
- Additional indirection for engineers prototyping prompts.
- Schema validation may reject valid-but-unexpected model output; requires retry/degrade handling.

### Neutral / follow-up

- Prompt templates and versioning live in `packages/ai` or database (future ADR).
- Video frame AI analysis invoked from worker through same package, not separate vendor integration.

## Related

- `docs/AI_POLICY.md`
- `adr/ADR-003-provider-agnostic-live.md` — `ai_analysis` capability
- `adr/ADR-004-entitlement-based-feature-access.md`
