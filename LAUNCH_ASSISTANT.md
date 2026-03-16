# Thorpe Workforce Launch Assistant

This assistant helps you finish all launch tasks that still require manual account/DNS actions.

## 1) Quick start

Print the remaining manual tasks:

```bash
python infrastructure/launch_assistant.py checklist
```

Run production verification checks:

```bash
python infrastructure/launch_assistant.py verify --api-url https://api.thorpeworkforce.ai --app-url https://thorpeworkforce.ai
```

The verification checks:

- DNS resolution for API host
- TLS handshake for API host
- backend health endpoints (`/health`, `/health/live`, `/health/ready`)
- CORS preflight response for your frontend origin

## 2) Railway setup source of truth

Use:

- `infrastructure/railway.md`
- `backend/railway.json`
- `backend/Procfile`
- `backend/scripts/start-web.sh`
- `backend/scripts/start-worker.sh`

## 3) One-shot operator prompt (for a human/agent)

Use this prompt with your deployment operator:

> Deploy Thorpe Workforce backend on Railway using the repository `backend/` folder.  
> Create API + Worker services plus Postgres and Redis, attach domain `api.thorpeworkforce.ai`, configure env vars from `infrastructure/railway.md`, and ensure API health endpoints pass.  
> Then set frontend env (`NEXT_PUBLIC_API_BASE_URL=https://api.thorpeworkforce.ai`, `NEXT_PUBLIC_APP_URL=https://thorpeworkforce.ai`) and run `python infrastructure/launch_assistant.py verify --api-url https://api.thorpeworkforce.ai --app-url https://thorpeworkforce.ai`.  
> Return a checklist with each item marked pass/fail and include exact failing endpoints/headers if any checks fail.
