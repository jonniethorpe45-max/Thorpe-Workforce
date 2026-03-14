from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models import Campaign, Worker, WorkerRun, WorkerRunStatus, WorkerStatus
from app.services.audit import log_audit_event
from app.workers.actions import WorkerActionRegistry, get_default_worker_action_registry
from app.workers.definitions import get_worker_definition
from app.workers.plan import WorkerRunContext
from app.workers.plan_builder import WorkerPlanBuilder


class WorkerExecutor:
    def __init__(
        self,
        plan_builder: WorkerPlanBuilder | None = None,
        action_registry: WorkerActionRegistry | None = None,
    ) -> None:
        self.plan_builder = plan_builder or WorkerPlanBuilder()
        self.action_registry = action_registry or get_default_worker_action_registry()

    @staticmethod
    def _merge_metrics(metrics: dict[str, Any], result: dict[str, Any]) -> None:
        for key, value in result.items():
            if isinstance(value, (int, float)) and isinstance(metrics.get(key), (int, float)):
                metrics[key] = metrics[key] + value
            else:
                metrics[key] = value

    def run_campaign_loop(
        self,
        db: Session,
        worker: Worker,
        campaign: Campaign,
        require_manual_approval: bool = True,
        run: WorkerRun | None = None,
    ) -> WorkerRun:
        now = datetime.now(UTC)
        definition = get_worker_definition(worker.worker_type)
        plan = self.plan_builder.build_plan(worker=worker, campaign=campaign, definition=definition)
        if run is None:
            run = WorkerRun(
                worker_id=worker.id,
                campaign_id=campaign.id,
                run_type="worker_execution",
                status=WorkerRunStatus.QUEUED.value,
                input_json={
                    "campaign_id": str(campaign.id),
                    "require_manual_approval": require_manual_approval,
                    "worker_type": worker.worker_type,
                    "plan_version": plan.plan_version,
                },
            )
            db.add(run)
            db.flush()

        run.status = WorkerRunStatus.RUNNING.value
        worker.status = WorkerStatus.PROSPECTING.value
        worker.last_error_text = None
        worker.plan_version = plan.plan_version
        worker.allowed_actions = list(plan.allowed_actions)
        run.started_at = run.started_at or now
        log_audit_event(
            db,
            workspace_id=worker.workspace_id,
            actor_type="system",
            actor_id="worker_executor",
            event_name="worker_run_started",
            payload={"worker_id": str(worker.id), "campaign_id": str(campaign.id), "run_id": str(run.id)},
        )
        run.input_json = {
            "campaign_id": str(campaign.id),
            "require_manual_approval": require_manual_approval,
            "worker_type": worker.worker_type,
            "plan_version": plan.plan_version,
            "allowed_actions": plan.allowed_actions,
            "steps": [
                {"key": step.key, "action_key": step.action_key, "status": step.status, "config": step.config} for step in plan.steps
            ],
        }
        context = WorkerRunContext(
            db=db,
            worker=worker,
            campaign=campaign,
            run=run,
            require_manual_approval=require_manual_approval,
            plan=plan,
            metrics={"emails_sent": 0, "drafts_generated": 0, "researched": 0},
        )

        try:
            for step in plan.steps:
                if step.status:
                    worker.status = step.status
                if step.action_key not in plan.allowed_actions:
                    raise ValueError(f"Action {step.action_key} is not allowed for worker_type {plan.worker_type}")
                step_result = self.action_registry.execute(step.action_key, context, step)
                self._merge_metrics(context.metrics, step_result)
                context.step_logs.append(
                    {
                        "step_key": step.key,
                        "action_key": step.action_key,
                        "status": "completed",
                        "result": step_result,
                    }
                )

            run.status = WorkerRunStatus.COMPLETED.value
            run.output_json = {
                **context.metrics,
                "selected_leads": len(context.selected_lead_ids),
                "suppressed_candidates": len(context.skipped_leads),
                "skipped_leads": context.skipped_leads,
                "step_logs": context.step_logs,
            }
            worker.last_run_at = datetime.now(UTC)
            worker.next_run_at = worker.last_run_at + timedelta(minutes=max(worker.run_interval_minutes, 15))
            if not context.selected_lead_ids:
                worker.status = WorkerStatus.IDLE.value
            elif require_manual_approval and int(context.metrics.get("drafts_generated", 0)) > 0:
                worker.status = WorkerStatus.AWAITING_APPROVAL.value
            else:
                worker.status = WorkerStatus.MONITORING.value
            log_audit_event(
                db,
                workspace_id=worker.workspace_id,
                actor_type="system",
                actor_id="worker_executor",
                event_name="worker_run_completed",
                payload={"run_id": str(run.id), "campaign_id": str(campaign.id), "output": run.output_json},
            )
            return run
        except Exception as exc:
            run.status = WorkerRunStatus.FAILED.value
            run.error_text = str(exc)
            worker.status = WorkerStatus.ERROR.value
            worker.last_error_text = str(exc)
            worker.last_run_at = datetime.now(UTC)
            worker.next_run_at = worker.last_run_at + timedelta(minutes=15)
            log_audit_event(
                db,
                workspace_id=worker.workspace_id,
                actor_type="system",
                actor_id="worker_executor",
                event_name="worker_run_failed",
                payload={
                    "run_id": str(run.id),
                    "campaign_id": str(campaign.id),
                    "error": str(exc),
                    "step_logs": context.step_logs,
                },
            )
            raise
        finally:
            run.finished_at = datetime.now(UTC)
