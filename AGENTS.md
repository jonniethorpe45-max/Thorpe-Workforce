# AGENTS.md

## Cursor Cloud specific instructions

This repo contains **two independent products** in one tree:

1. **Thorpe Desktop** (primary deliverable) — Tauri 2 + Rust + React/Vite at the repo root (`src/`, `src-tauri/`). Local-first AI IT-support app; data in bundled SQLite, no external services. Docs: `THORPE.md`, `BUILD.md`.
2. **Thorpe Workforce SaaS** (secondary) — Next.js frontend in `frontend/` + FastAPI/Celery backend in `backend/`. Docs: `README.md`.

The startup update script already runs: `npm install` (root), `npm install --prefix frontend`, and creates `backend/.venv` + installs `backend/requirements.txt`. Everything below is about *running* the services, not installing deps.

### Environment notes (already provisioned in the snapshot)
- System libs for Tauri (`libwebkit2gtk-4.1-dev`, `libayatana-appindicator3-dev`, `librsvg2-dev`, GTK/build-essential, `libssl-dev`) are installed.
- Postgres 16 and Redis 7 are installed **natively** (no Docker in this VM). `docker-compose.yml` exists but Docker is not available; use the native services instead.
- A GUI desktop is available on `DISPLAY=:1` (needed to launch the Tauri window).
- The Tauri Rust target dir (`src-tauri/target/`) is gitignored; the first `tauri:dev`/`cargo build` after a cold target is slow (~1 min), fast afterwards.

### Thorpe Desktop (root) — lint / test / build / run
- Lint: `npm run lint` (tsc). Tests: `npm run test` (vitest). Web-only build: `npm run build`.
- Run the full desktop app: `DISPLAY=:1 npm run tauri:dev`. The window title is "Thorpe — AI IT Support". Core flow = Dashboard → "Start New Scan" → consent → real system diagnostics.
- Icons in `src-tauri/icons/` are committed; only re-run `bash scripts/generate-icons.sh` if they are missing.
- libEGL/DRI3 warnings on launch are harmless (software rendering fallback); the window still renders.
- Plain `npm run dev` (Vite, port 1420) serves a UI-only preview backed by mock data (`src/services/mock.ts`) when not running inside Tauri.

### Thorpe Workforce SaaS — run order
Start the native datastores first (they are not auto-started; no systemd in this container):
- Postgres: `sudo pg_ctlcluster 16 main start` (db `thorpe_workforce`, user/pass `postgres`/`postgres`).
- Redis: `sudo redis-server --daemonize yes --port 6379`.

Backend (`backend/`, use the venv at `backend/.venv`):
- Create env once: `cp .env.example .env`, then **delete the four trailing `RUN_MIGRATIONS_ON_START` / `RUN_SEEDS_ON_START` / `CELERY_LOG_LEVEL` / `UVICORN_HOST` lines** — the pydantic `Settings` model uses `extra=forbid` and will crash on those Railway-only vars. (They are shell vars for the Railway start scripts, not for the app `.env`.)
- Migrate + seed: `.venv/bin/alembic upgrade head`, `.venv/bin/python scripts/seed_worker_system.py`, `.venv/bin/python scripts/seed_demo.py`.
- API: `.venv/bin/uvicorn app.main:app --reload --port 8000`. Celery (separate process): `.venv/bin/celery -A app.tasks.celery_app.celery_app worker -l info`.
- Tests: `.venv/bin/pytest`. Health: `GET /health/ready` reports DB status.

Frontend (`frontend/`):
- Once: `cp .env.example .env.local`. Run: `npm run dev` (port 3000). Lint: `npm run lint`.
- Demo login (after seeding): `demo@thorpeworkforce.com` / `DemoPass123!`.
- All AI/email/calendar/billing providers default to mock/placeholder, so the SaaS runs fully locally without third-party keys.
