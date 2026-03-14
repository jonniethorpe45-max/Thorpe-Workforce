from datetime import UTC, datetime, timedelta
import uuid

from sqlalchemy.orm import Session

from app.models import Campaign, Lead, Worker, WorkerRun, WorkerRunStatus, WorkerStatus
from app.services.analytics_recorder import record_worker_signal
from app.services.audit import log_audit_event
from app.services.lead_researcher import research_lead
from app.services.message_generator import generate_initial_sequence, send_approved_messages
from app.workers.planner import WorkerPlanner


class WorkerExecutor:
    def __init__(self) -> None:
        self.planner = WorkerPlanner()

    def run_campaign_loop(
        self,
        db: Session,
        worker: Worker,
        campaign: Campaign,
        require_manual_approval: bool = True,
        run: WorkerRun | None = None,
    ) -> WorkerRun:
        now = datetime.now(UTC)
        if run is None:
            run = WorkerRun(
                worker_id=worker.id,
                campaign_id=campaign.id,
                run_type="campaign_loop",
                status=WorkerRunStatus.QUEUED.value,
                input_json={"campaign_id": str(campaign.id), "require_manual_approval": require_manual_approval},
            )
            db.add(run)
            db.flush()

        run.status = WorkerRunStatus.RUNNING.value
        worker.status = WorkerStatus.PROSPECTING.value
        worker.last_error_text = None
        run.started_at = run.started_at or now
        log_audit_event(
            db,
            workspace_id=worker.workspace_id,
            actor_type="system",
            actor_id="worker_executor",
            event_name="worker_run_started",
            payload={"worker_id": str(worker.id), "campaign_id": str(campaign.id), "run_id": str(run.id)},
        )

        plan = self.planner.build_execution_plan(db, worker, campaign)
        lead_ids: list[str] = plan.get("lead_ids", [])
        output: dict[str, int | list[dict[str, str]]] = {
            "selected_leads": len(lead_ids),
            "researched": 0,
            "drafts_generated": 0,
            "emails_sent": 0,
            "suppressed_candidates": len(plan.get("skipped_leads", [])),
            "skipped_leads": plan.get("skipped_leads", []),
        }
        run.input_json = {
            "campaign_id": str(campaign.id),
            "require_manual_approval": require_manual_approval,
            "plan": plan,
        }

        try:
            worker.status = WorkerStatus.RESEARCHING.value
            for lead_id in lead_ids:
                parsed_lead_id = uuid.UUID(lead_id) if isinstance(lead_id, str) else lead_id
                lead = db.get(Lead, parsed_lead_id)
                if not lead:
                    continue
                research_lead(db, lead, industry_hint=campaign.target_industry)
                output["researched"] = int(output["researched"]) + 1

            worker.status = WorkerStatus.DRAFTING.value
            for lead_id in lead_ids:
                parsed_lead_id = uuid.UUID(lead_id) if isinstance(lead_id, str) else lead_id
                lead = db.get(Lead, parsed_lead_id)
                if not lead:
                    continue
                generated = generate_initial_sequence(
                    db,
                    campaign=campaign,
                    lead=lead,
                    require_approval=require_manual_approval,
                )
                output["drafts_generated"] = int(output["drafts_generated"]) + len(generated)

            if require_manual_approval:
                worker.status = WorkerStatus.AWAITING_APPROVAL.value
            else:
                worker.status = WorkerStatus.SENDING.value
                output["emails_sent"] = send_approved_messages(db, workspace_id=worker.workspace_id, campaign_id=campaign.id)
                worker.status = WorkerStatus.MONITORING.value

            if not lead_ids:
                worker.status = WorkerStatus.OPTIMIZING.value
                record_worker_signal(
                    db,
                    workspace_id=worker.workspace_id,
                    actor_id=str(worker.id),
                    signal_name="no_eligible_leads",
                    payload={"campaign_id": str(campaign.id)},
                )
                worker.status = WorkerStatus.IDLE.value

            run.status = WorkerRunStatus.COMPLETED.value
            run.output_json = output
            worker.last_run_at = datetime.now(UTC)
            worker.next_run_at = worker.last_run_at + timedelta(minutes=max(worker.run_interval_minutes, 15))
            if worker.status not in {WorkerStatus.AWAITING_APPROVAL.value, WorkerStatus.MONITORING.value, WorkerStatus.IDLE.value}:
                worker.status = WorkerStatus.MONITORING.value
            log_audit_event(
                db,
                workspace_id=worker.workspace_id,
                actor_type="system",
                actor_id="worker_executor",
                event_name="worker_run_completed",
                payload={"run_id": str(run.id), "campaign_id": str(campaign.id), "output": output},
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
                payload={"run_id": str(run.id), "campaign_id": str(campaign.id), "error": str(exc)},
            )
            raise
        finally:
            run.finished_at = datetime.now(UTC)
