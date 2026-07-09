# DevOps Builder Handoff — Build Zero v1.6

## Mission

Take the Genesis Build Zero monorepo under `genesis/` and make local/prod orchestration reliable.

## Completed by Frontend/App Builder

- React Jonathan Web + Admin Console
- TypeScript + Python SDKs
- Core FastAPI services with gateway-first flow
- SQLite approvals/audit persistence
- `tools/start-dev.sh` process starter
- Draft `infrastructure/docker-compose.yml`

## Your job

1. Validate and harden Docker Compose networking between services.
2. Ensure healthchecks and dependency order (registry/calendar before core; core before gateway).
3. Add CI workflow for Python tests + frontend lint/build/test.
4. Document env vars (`GENESIS_ENV`, `*_URL`, `VITE_GATEWAY_URL`).
5. Produce a handoff for Security Review AI.

## Constraints

- Do not bypass gateway, policy, approval, or audit.
- Read `GENESIS_MANIFEST.md`, `BUILD_ZERO_BACKLOG.md`, and `AI_BUILDER_HANDOFF_V1_6.md`.
- Update ADRs for infrastructure decisions.

## Suggested first commands

```bash
cd genesis
pip install -r requirements.txt
bash tools/start-dev.sh
cd packages/sdk/typescript && npm install && npm run build && npm test
cd ../../apps/jonathan-web && npm install && npm test && npm run build
cd ../admin-console && npm install && npm test && npm run build
```
