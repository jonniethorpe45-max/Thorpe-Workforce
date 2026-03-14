import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import WorkerMemory, WorkerMemoryScope
from app.services.ai_utils import normalize_whitespace


def _normalize_scope(scope: WorkerMemoryScope | str | None) -> str:
    raw = scope.value if isinstance(scope, WorkerMemoryScope) else str(scope or WorkerMemoryScope.INSTANCE.value)
    if raw not in {item.value for item in WorkerMemoryScope}:
        return WorkerMemoryScope.INSTANCE.value
    return raw


def _normalize_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {"value": value}


def _normalize_memory_key(memory_key: str) -> str:
    key = normalize_whitespace(memory_key)
    if not key:
        raise HTTPException(status_code=400, detail="memory_key is required")
    return key[:255]


def _resolve_target_instance_id(
    *,
    scope: str,
    instance_id: uuid.UUID | None,
) -> uuid.UUID | None:
    if scope == WorkerMemoryScope.NONE.value:
        return None
    if scope == WorkerMemoryScope.WORKSPACE.value:
        return None
    if not instance_id:
        raise HTTPException(status_code=400, detail="instance_id is required for instance memory scope")
    return instance_id


def upsert_worker_memory(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    memory_key: str,
    memory_value: Any,
    scope: WorkerMemoryScope | str,
    instance_id: uuid.UUID | None = None,
    template_id: uuid.UUID | None = None,
    memory_type: str = "episodic",
) -> WorkerMemory | None:
    normalized_scope = _normalize_scope(scope)
    if normalized_scope == WorkerMemoryScope.NONE.value:
        return None

    key = _normalize_memory_key(memory_key)
    target_instance_id = _resolve_target_instance_id(scope=normalized_scope, instance_id=instance_id)
    payload = _normalize_payload(memory_value)

    query = db.query(WorkerMemory).filter(
        WorkerMemory.workspace_id == workspace_id,
        WorkerMemory.memory_key == key,
    )
    if target_instance_id is None:
        query = query.filter(WorkerMemory.instance_id.is_(None))
    else:
        query = query.filter(WorkerMemory.instance_id == target_instance_id)
    record = query.first()

    if record:
        record.memory_value_json = payload
        record.template_id = template_id or record.template_id
        record.memory_type = memory_type or record.memory_type
        db.flush()
        return record

    memory = WorkerMemory(
        workspace_id=workspace_id,
        instance_id=target_instance_id,
        template_id=template_id,
        memory_key=key,
        memory_value_json=payload,
        memory_type=memory_type or "episodic",
    )
    db.add(memory)
    db.flush()
    return memory


def read_worker_memory(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    scope: WorkerMemoryScope | str,
    instance_id: uuid.UUID | None = None,
    template_id: uuid.UUID | None = None,
    memory_key: str | None = None,
    limit: int = 100,
) -> list[WorkerMemory]:
    normalized_scope = _normalize_scope(scope)
    if normalized_scope == WorkerMemoryScope.NONE.value:
        return []

    query = db.query(WorkerMemory).filter(WorkerMemory.workspace_id == workspace_id)
    if normalized_scope == WorkerMemoryScope.INSTANCE.value:
        if not instance_id:
            raise HTTPException(status_code=400, detail="instance_id is required for instance memory scope")
        query = query.filter(WorkerMemory.instance_id == instance_id)
    else:
        query = query.filter(or_(WorkerMemory.instance_id.is_(None), WorkerMemory.instance_id == instance_id))

    if template_id:
        query = query.filter(or_(WorkerMemory.template_id.is_(None), WorkerMemory.template_id == template_id))
    if memory_key:
        query = query.filter(WorkerMemory.memory_key == _normalize_memory_key(memory_key))
    return query.order_by(WorkerMemory.updated_at.desc()).limit(max(limit, 1)).all()


def build_worker_memory_bundle(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    scope: WorkerMemoryScope | str,
    instance_id: uuid.UUID | None = None,
    template_id: uuid.UUID | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    records = read_worker_memory(
        db,
        workspace_id=workspace_id,
        scope=scope,
        instance_id=instance_id,
        template_id=template_id,
        limit=limit,
    )
    bundle: dict[str, Any] = {}
    for record in records:
        key = normalize_whitespace(record.memory_key)
        if not key or key in bundle:
            continue
        bundle[key] = record.memory_value_json
    return bundle


def store_worker_run_context(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    scope: WorkerMemoryScope | str,
    instance_id: uuid.UUID | None,
    template_id: uuid.UUID | None,
    run_id: uuid.UUID,
    summary: str,
    runtime_input: dict[str, Any],
    output: dict[str, Any],
    suggested_actions: list[str] | None,
    notes: list[str] | None,
    token_usage_input: int,
    token_usage_output: int,
    cost_cents: int,
) -> None:
    normalized_scope = _normalize_scope(scope)
    if normalized_scope == WorkerMemoryScope.NONE.value:
        return

    upsert_worker_memory(
        db,
        workspace_id=workspace_id,
        memory_key="last_run_summary",
        memory_value={"summary": summary},
        scope=normalized_scope,
        instance_id=instance_id,
        template_id=template_id,
        memory_type="run_context",
    )
    upsert_worker_memory(
        db,
        workspace_id=workspace_id,
        memory_key="last_runtime_input",
        memory_value=runtime_input,
        scope=normalized_scope,
        instance_id=instance_id,
        template_id=template_id,
        memory_type="run_context",
    )
    upsert_worker_memory(
        db,
        workspace_id=workspace_id,
        memory_key="last_run_output",
        memory_value=output,
        scope=normalized_scope,
        instance_id=instance_id,
        template_id=template_id,
        memory_type="run_context",
    )
    upsert_worker_memory(
        db,
        workspace_id=workspace_id,
        memory_key="last_run_metadata",
        memory_value={
            "run_id": str(run_id),
            "suggested_actions": suggested_actions or [],
            "notes": notes or [],
            "token_usage_input": token_usage_input,
            "token_usage_output": token_usage_output,
            "cost_cents": cost_cents,
            "recorded_at": datetime.now(UTC).isoformat(),
        },
        scope=normalized_scope,
        instance_id=instance_id,
        template_id=template_id,
        memory_type="run_context",
    )
