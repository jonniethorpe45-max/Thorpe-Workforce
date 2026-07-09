# Genesis Monorepo (Build Zero)

The unified engineering workspace for Project Genesis and Thorpe Technologies.

## Mission

Build Jonathan, the Universal Intent Layer, Thorpe Cloud OS, and the Genesis Platform from one coordinated engineering foundation.

## Structure

```text
apps/
  jonathan-web/       React + TypeScript client for Jonathan
  admin-console/      React + TypeScript enterprise administration portal
  cloud-os/           Future Thorpe Cloud OS workspace

services/
  jonathan-core/      Intent → Plan → Policy → Orchestration → Explanation → Audit
  knowledge-graph/    Structured source of truth for Genesis
  identity/           Authentication, organizations, users, roles
  capability-registry/ Registered capabilities and connectors
  mock-calendar/      Demo calendar connector
  api-gateway/        Gateway-first entry point
  model-router/       Model routing placeholder

packages/
  schemas/            Shared data contracts
  sdk/python/         Python SDK
  sdk/typescript/     TypeScript SDK
  shared/             Common utilities

docs/                 Architecture, security, ADRs
tools/                Builder and automation tools
tests/                Cross-service tests
```

## Current Version

**Build Zero v1.6** — React + TypeScript frontends for Jonathan Web and Admin Console, using the Genesis TypeScript SDK with gateway-first architecture.

## Core Flow

```text
User → Jonathan Web → API Gateway → Jonathan Core → Capability Registry → Approval → Execute → Mock Calendar → Audit
```

## Quick Start

See [RUNBOOK.md](./RUNBOOK.md).

## AI Pipeline

See [MASTER_AI_BUILDER_PIPELINE.md](./MASTER_AI_BUILDER_PIPELINE.md) and `tools/ai-pipeline/`.
