# ScoutAI architecture

## Intent

ScoutAI turns a research question into a structured intelligence brief:

1. Accept query + focus + depth
2. Synthesize findings (live LLM or demo corpus)
3. Return summary, findings, risks, next actions, and sources

## Components

| Piece | Role |
| --- | --- |
| `frontend/` | Next.js marketing surface + scout workspace UI |
| `backend/` | FastAPI `/health` and `/research` endpoints |
| `docker-compose.yml` | Local full stack |

## Modes

- **Demo** — no `OPENAI_API_KEY` (or `SCOUTAI_DEMO_MODE=always`)
- **Live** — OpenAI-compatible chat completions with JSON object responses

Live failures fall back to demo briefs so the product stays usable.

## Extracting to its own GitHub repo

Cursor cloud agents for this environment only have write access to
`jonniethorpe45-max/Thorpe-Workforce` and cannot call `POST /user/repos`.

Use `scripts/create-github-repo.sh` from an account that can create repositories
under `jonniethorpe45-max`, then reconnect Cursor to the new remote.
