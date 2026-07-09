# Project Genesis Master AI Builder Pipeline v1.0

## Primary Builder Selection

### Selected Primary Builder: Cursor

Cursor is the primary hands-on builder for converting static frontend prototypes into real React + TypeScript applications.

## Supporting Builders

- GitHub Copilot Coding Agent — issue-based PRs
- Security Review AI
- DevOps Builder
- QA/Test Builder
- Documentation Builder
- Chief Architect Final Review

## Current Build State

Build Zero v1.6 includes:

- Jonathan Core, Knowledge Graph, Identity, Capability Registry, Mock Calendar
- API Gateway, Model Router
- React Jonathan Web + Admin Console
- Python SDK + TypeScript SDK
- SQLite persistence for approvals and audit
- ADRs through ADR-0020

## Builder Chain

```text
Chief Architect
      ↓
Cursor Frontend/App Builder   ← completed in v1.6
      ↓
DevOps Builder                ← next
      ↓
Security Review AI
      ↓
QA/Test Builder
      ↓
Documentation Builder
      ↓
Chief Architect Final Review
```

## Pipeline Rule

No builder may skip:

- Reading GENESIS_MANIFEST.md
- Reading BUILD_ZERO_BACKLOG.md
- Reading AI_BUILDER_HANDOFF docs
- Preserving policy, approval, audit, and gateway-first architecture
- Updating documentation
- Creating or updating ADRs for major changes
- Producing a handoff for the next builder
