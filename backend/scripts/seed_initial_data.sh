#!/usr/bin/env bash
set -euo pipefail

python scripts/seed_worker_system.py

if [[ "${SEED_DEMO_DATA:-false}" == "true" ]]; then
  python scripts/seed_demo.py
fi

python - <<'PY'
from app.db.session import SessionLocal
from app.models import User, Workspace
from app.services.founder_os import ensure_founder_os_chains

db = SessionLocal()
try:
    workspaces = db.query(Workspace).all()
    for workspace in workspaces:
        owner_or_admin = (
            db.query(User)
            .filter(User.workspace_id == workspace.id, User.role.in_(("owner", "admin", "super_admin")))
            .order_by(User.created_at.asc())
            .first()
        )
        ensure_founder_os_chains(
            db,
            workspace_id=workspace.id,
            actor_user_id=owner_or_admin.id if owner_or_admin else None,
        )
    db.commit()
finally:
    db.close()
PY
