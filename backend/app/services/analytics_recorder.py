from sqlalchemy.orm import Session

from app.services.audit import log_audit_event


def record_worker_signal(db: Session, workspace_id, actor_id: str, signal_name: str, payload: dict | None = None) -> None:
    log_audit_event(
        db,
        workspace_id=workspace_id,
        actor_type="system",
        actor_id=actor_id,
        event_name=f"optimization_signal:{signal_name}",
        payload=payload or {},
    )
