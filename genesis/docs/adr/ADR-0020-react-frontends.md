# ADR-0020: React + TypeScript Frontends for Build Zero

## Status

Accepted

## Context

Build Zero v1.4 shipped static HTML prototypes for Jonathan Web and Admin Console. The Master AI Builder Pipeline selected Cursor as Frontend/App Builder to convert these into maintainable React + TypeScript applications using the Genesis TypeScript SDK.

## Decision

1. Implement `apps/jonathan-web` and `apps/admin-console` as Vite + React + TypeScript apps.
2. Route all frontend API calls through the API Gateway via `@genesis/sdk`.
3. Extract reusable UI into `packages/ui` (intent form, approval card, execution result, audit list, service catalog, capability catalog).
4. Do not add direct Jonathan Core calls from the browser in default mode.

## Consequences

- Frontends remain gateway-first and cannot bypass approval/policy/audit.
- DevOps must serve static builds and configure `VITE_GATEWAY_URL`.
- Shared UI package simplifies Admin Console and Jonathan Web consistency.
