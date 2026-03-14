from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.models import Campaign, Worker, WorkerRun


@dataclass
class WorkerStep:
    key: str
    name: str
    action_key: str
    status: str | None = None
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkerPlan:
    worker_type: str
    plan_version: str
    allowed_actions: list[str]
    steps: list[WorkerStep]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkerRunContext:
    db: Session
    worker: Worker
    campaign: Campaign
    run: WorkerRun
    require_manual_approval: bool
    plan: WorkerPlan
    selected_lead_ids: list[str] = field(default_factory=list)
    skipped_leads: list[dict[str, str]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    step_logs: list[dict[str, Any]] = field(default_factory=list)
