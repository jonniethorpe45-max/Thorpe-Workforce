# AI Builder Handoff — Build Zero v1.6

## Current State

Project Genesis Build Zero now includes React + TypeScript frontends:

- Jonathan Core
- Knowledge Graph
- Identity placeholder
- Capability Registry
- Mock Calendar connector
- API Gateway
- Model Router placeholder
- **Jonathan Web (React + TypeScript + Vite)**
- **Admin Console (React + TypeScript + Vite)**
- Python SDK
- TypeScript SDK
- SQLite persistence for Jonathan approvals/audit
- ADRs through ADR-0020

## Core Flow

User → API Gateway → Jonathan Core → Capability Registry → Approval → Execute → Mock Calendar → Audit

## What Changed in v1.6

- Converted static HTML prototypes into maintainable React apps
- Shared UI components for intent, approvals, execution, audit, services, capabilities
- Both apps use `@genesis/sdk` and call the API Gateway only
- No bypass of approval, policy, or audit

## Next Best Builder

DevOps Builder — Docker Compose validity, service networking, CI, and deployment scaffolding.

## Recommended Next Builder Prompt

See `tools/ai-pipeline/DEVOPS_BUILDER_HANDOFF.md`.

## Do Not Proceed Without Human Review

Before production deployment, the following need specialist review:

- Security architecture
- Authentication provider selection
- Docker Compose validity and service networking
- API schema normalization
- Database migration strategy
