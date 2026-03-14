from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog


def log_audit_event(
    db: Session,
    workspace_id,
    actor_type: str,
    actor_id: str,
    event_name: str,
    payload: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditLog(
            workspace_id=workspace_id,
            actor_type=actor_type,
            actor_id=actor_id,
            event_name=event_name,
            payload_json=payload or {},
        )
    )
