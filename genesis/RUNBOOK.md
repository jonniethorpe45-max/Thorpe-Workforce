# Genesis Build Zero Runbook

## 1. Install Python Dependencies

```bash
cd genesis
pip install -r requirements.txt
```

## 2. Run Services (separate terminals)

| Service | Port | Command |
|---------|------|---------|
| API Gateway | 7999 | `cd services/api-gateway && uvicorn app.main:app --reload --port 7999` |
| Jonathan Core | 8000 | `cd services/jonathan-core && uvicorn app.main:app --reload --port 8000` |
| Knowledge Graph | 8001 | `cd services/knowledge-graph && uvicorn app.main:app --reload --port 8001` |
| Identity | 8002 | `cd services/identity && uvicorn app.main:app --reload --port 8002` |
| Capability Registry | 8003 | `cd services/capability-registry && uvicorn app.main:app --reload --port 8003` |
| Mock Calendar | 8004 | `cd services/mock-calendar && uvicorn app.main:app --reload --port 8004` |
| Model Router | 8005 | `cd services/model-router && uvicorn app.main:app --reload --port 8005` |

Or use the helper:

```bash
bash tools/start-dev.sh
```

## 3. Frontends

```bash
# TypeScript SDK
cd packages/sdk/typescript && npm install && npm run build

# Jonathan Web
cd apps/jonathan-web && npm install && npm run dev
# → http://localhost:5173

# Admin Console
cd apps/admin-console && npm install && npm run dev
# → http://localhost:5174
```

## 4. Success Criteria

A user can type a request into Jonathan Web and receive:

- Structured intent
- Plan
- Policy decision
- Approval (when required)
- Execution result
- Explanation
- Audit event

All through the API Gateway (`http://localhost:7999`).

## Gateway Endpoints

```text
POST /gateway/intent
POST /gateway/approvals/approve
POST /gateway/execute
GET  /gateway/audit
GET  /gateway/approvals
```

## Reset Local DB

```bash
python tools/reset_jonathan_db.py
```
