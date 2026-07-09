# AGENTS.md

## Cursor Cloud specific instructions

This repository is a **two-product monorepo**. The two products are independent and do not talk to each other:

1. **Thorpe Desktop** (primary) — an AI-powered IT-support desktop app. Code at the repo root: `src/` (React + Vite + TypeScript) and `src-tauri/` (Rust/Tauri). See `THORPE.md`.
2. **Thorpe Workforce** (secondary) — an AI-workforce SaaS. `backend/` (FastAPI + SQLAlchemy + Alembic + Celery) and `frontend/` (Next.js). See `README.md`.

The startup update script already refreshes dependencies (`npm install` at root and in `frontend/`, and a `backend/.venv` with `pip install -r backend/requirements.txt`). System packages (PostgreSQL 16, Redis 7, `python3-venv`, and the Tauri GTK/WebKit dev libraries) are baked into the VM image, so they are **not** reinstalled on startup.

### Services and how to run them

Standard commands live in `README.md` (Workforce) and `THORPE.md` (Desktop). Notable caveats below.

| Service | Dir | Dev command | Port |
|---|---|---|---|
| Workforce backend (FastAPI) | `backend` | `source .venv/bin/activate && uvicorn app.main:app --reload --port 8000` | 8000 |
| Workforce frontend (Next.js) | `frontend` | `npm run dev` | 3000 |
| Desktop web preview (Vite) | repo root | `npm run dev` | 1420 |

### Non-obvious caveats (read before starting services)

- **Databases are native, not Docker.** `docker-compose.yml` is the documented path, but Docker is not installed; PostgreSQL and Redis are installed natively. systemd is not running in the VM, so start them manually and idempotently:
  - `sudo pg_ctlcluster 16 main start`
  - `sudo redis-server --daemonize yes`
  - DB is `thorpe_workforce`, user/password `postgres`/`postgres` (matches `backend/.env.example` `DATABASE_URL`). If the role has no password yet: `sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';"`.
- **`backend/.env` gotcha:** copy `backend/.env.example` to `backend/.env`, then **delete the trailing "Railway runtime toggles" block** (`RUN_MIGRATIONS_ON_START`, `RUN_SEEDS_ON_START`, `CELERY_LOG_LEVEL`, `UVICORN_HOST`). `app/core/config.py` `Settings` forbids extra keys, so leaving them causes a pydantic `extra_forbidden` ValidationError on any backend/alembic command. Those toggles are only consumed by `scripts/start-web.sh`/`start-worker.sh` via the shell, not by the app.
- **Workforce DB init:** from `backend/` with the venv active, run `alembic upgrade head`, then `python scripts/seed_worker_system.py` and `python scripts/seed_demo.py`. Seed demo login: `demo@thorpeworkforce.com` / `DemoPass123!`.
- **Desktop UI in the cloud VM:** the full Tauri shell (`npm run tauri:dev`) needs a desktop/display and is not suitable headless. Use the **Vite web preview** (`npm run dev`, port 1420) which renders the same React UI with mock data.
- **Rust tests / Tauri build need the built frontend.** `cargo test` (and any tauri build) invokes `tauri::generate_context!()` which requires `dist/` to exist (`frontendDist = "../dist"`). Run `npm run build` at the repo root first, otherwise the Rust build fails with "The `frontendDist` configuration is set to `\"../dist\"` but this path doesn't exist".

### Lint / test / build quick reference

- Desktop: `npm run lint` (tsc), `npm run test` (Vitest), `cargo test` in `src-tauri` (after `npm run build`), `npm run build`.
- Workforce backend: `cd backend && source .venv/bin/activate && pytest` (needs Postgres + Redis running).
- Workforce frontend: `cd frontend && npm run lint`, `npm run build`.
