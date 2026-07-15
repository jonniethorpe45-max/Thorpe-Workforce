# ScoutAI agent notes

## Product

ScoutAI is an AI research scout: query → structured intelligence brief (summary, findings, risks, next actions, sources).

## Stack

- `frontend/` — Next.js + TypeScript + Tailwind
- `backend/` — FastAPI
- Demo mode when `OPENAI_API_KEY` is unset

## When the repo is empty

Bootstrap from the Thorpe-Workforce `scoutai/` scaffold (PR #33) and place files at **repository root**.

## Quality bar

- Backend tests must pass
- Frontend must build
- Prefer clear product UX over new scope
- Keep commits and PRs focused on ScoutAI only
