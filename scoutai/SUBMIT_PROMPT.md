# Submit a prompt on ScoutAI

Cursor cloud agents need a **real GitHub repository** selected before you can submit a prompt. `jonniethorpe45-max/ScoutAI` does **not** exist yet, and Cursor’s GitHub App token **cannot create repos**.

## 1. Create the GitHub repo (about 1 minute)

### On phone (GitHub app or github.com)

1. Open **GitHub** → **+** → **New repository**
2. Owner: `jonniethorpe45-max`
3. Name: `ScoutAI`
4. Public
5. Description: `ScoutAI — AI research and scouting assistant`
6. Create repository (**empty is fine**)

### On computer (CLI)

```bash
gh repo create jonniethorpe45-max/ScoutAI \
  --public \
  --description "ScoutAI — AI research and scouting assistant"
```

Then publish this scaffold:

```bash
cd scoutai
bash scripts/create-github-repo.sh
```

## 2. Give Cursor access to ScoutAI

1. Open https://cursor.com/dashboard?tab=integrations
2. GitHub → **Connect** / **Manage**
3. Include **`jonniethorpe45-max/ScoutAI`** (or “All repositories”)
4. Save

Until Cursor’s GitHub App can access ScoutAI, the repo will not appear when starting an agent.

## 3. Submit this prompt

In the Cursor **iOS app** or https://cursor.com/agents:

1. Choose repository: **`jonniethorpe45-max/ScoutAI`**
2. Branch: **`main`**
3. Paste the prompt below → Send

### Starter prompt (copy all of it)

```text
You are working in the ScoutAI repository.

Goal: ship a polished AI research-scout product that turns a topic into a sourced intelligence brief.

If this repo is empty or only has a README:
1. Pull the full ScoutAI scaffold from Thorpe-Workforce PR #33 path scoutai/ (or recreate it):
   - frontend/: Next.js landing + scout workspace
   - backend/: FastAPI /health + /research (demo mode without API key; live mode with OpenAI-compatible key)
   - docker-compose.yml, .env.example, MIT LICENSE, docs/
2. Put that content at the repository root (not nested under scoutai/).
3. Commit, push, and open a PR.

If scaffold is already at repo root:
1. Harden the research flow (better prompts, clearer demo vs live UX, error handling).
2. Add a basic README quick-start that matches the actual layout.
3. Ensure backend tests pass and the frontend builds.
4. Open or update a PR with what changed.

Do not invent unrelated products. Keep branding as ScoutAI.
```

## Shortcut while ScoutAI is still empty

Until the new repo is created and connected, you can keep using this Thorpe-Workforce agent and say:

```text
Continue ScoutAI work in scoutai/ and keep PR #33 updated.
```

That does **not** substitute for selecting `ScoutAI` as the target repo once you want ScoutAI-only agents.
