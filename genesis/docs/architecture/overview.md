# Genesis Architecture Overview

## Gateway-first

Browsers and SDKs call the API Gateway. The gateway proxies to Jonathan Core, Knowledge Graph, and Capability Registry.

## Trust path

Intent → Plan → Policy (capability gate) → Approval (when required) → Execute → Audit

No feature may skip policy, approval, or audit.

## Services

| Service | Port | Role |
|---------|------|------|
| api-gateway | 7999 | Public entry |
| jonathan-core | 8000 | Intent orchestration |
| knowledge-graph | 8001 | Service catalog |
| identity | 8002 | Demo auth |
| capability-registry | 8003 | Capability catalog |
| mock-calendar | 8004 | Connector |
| model-router | 8005 | Model selection placeholder |

## Frontends

- Jonathan Web (`:5173`) — user intent experience
- Admin Console (`:5174`) — approvals, audit, catalogs
