# ScoutAI

**ScoutAI** is an AI research scout. Give it a topic, market, company, or question — it investigates sources, synthesizes findings, and returns a structured intelligence brief with citations.

> This folder is a **standalone repository scaffold**. It is currently hosted inside `Thorpe-Workforce` so the cloud agent can push it. Extract it to its own GitHub repo with the script below.

## Create the GitHub repository

From a machine authenticated as **jonniethorpe45-max** (personal `gh` login, not the Cursor install token):

```bash
cd scoutai
bash scripts/create-github-repo.sh
```

That creates `https://github.com/jonniethorpe45-max/ScoutAI`, pushes `main`, and leaves this folder as a clean standalone git history.

Manual alternative:

```bash
cd scoutai
gh repo create jonniethorpe45-max/ScoutAI \
  --public \
  --description "ScoutAI — AI research and scouting assistant" \
  --source=. \
  --remote=origin \
  --push
```

Then connect the new repo in Cursor Cloud Agents so future runs target ScoutAI directly.

## Product

| Capability | Description |
| --- | --- |
| Research briefs | Topic → structured findings, risks, and next actions |
| Source tracking | Claims tied to sources (demo + live modes) |
| Scout workspace | Paste a brief prompt and iterate on follow-ups |
| Demo mode | Works without API keys using curated sample briefs |

## Stack

- **Frontend** — Next.js 15, TypeScript, Tailwind CSS
- **Backend** — FastAPI (Python 3.11+)
- **AI** — OpenAI-compatible chat API (optional; demo mode when unset)

## Quick start

### Requirements

- Node.js 20+
- Python 3.11+
- (Optional) Docker / Docker Compose

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # from repo root if not already present
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Docker

```bash
docker compose up --build
```

- Web: http://localhost:3000  
- API: http://localhost:8000/docs  

## Environment

Copy `.env.example` → `.env`:

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Enables live research synthesis |
| `OPENAI_MODEL` | Default `gpt-4o-mini` |
| `OPENAI_BASE_URL` | Override for compatible providers |
| `NEXT_PUBLIC_API_URL` | Frontend → API base (default `http://localhost:8000`) |

Without `OPENAI_API_KEY`, ScoutAI runs in **demo mode** and returns sample briefs.

## Layout

```text
scoutai/
  frontend/     Next.js app (landing + scout workspace)
  backend/      FastAPI research API
  scripts/      Repo publish helpers
  docs/         Architecture notes
  docker-compose.yml
```

## License

MIT — see [LICENSE](./LICENSE).
