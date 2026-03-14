from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import Campaign, Lead, Worker, WorkerRun, WorkerStatus
from app.services.lead_researcher import research_lead
from app.services.message_generator import generate_initial_sequence, send_approved_messages
from app.workers.planner import WorkerPlanner


class WorkerExecutor:
    def __init__(self) -> None:
        self.planner = WorkerPlanner()

    def run_campaign_loop(self, db: Session, worker: Worker, campaign: Campaign, require_manual_approval: bool = True) -> WorkerRun:
        run = WorkerRun(
            worker_id=worker.id,
            run_type="campaign_loop",
            status="running",
            input_json={"campaign_id": str(campaign.id)},
        )
        db.add(run)
        worker.status = WorkerStatus.PROSPECTING.value
        plan = self.planner.build_execution_plan(db, worker, campaign)

        worker.status = WorkerStatus.RESEARCHING.value
        lead_ids = plan["lead_ids"]
        lead_count = 0
        for lead_id in lead_ids:
            lead = db.get(Lead, lead_id)
            if not lead:
                continue
            research_lead(db, lead)
            lead_count += 1

        worker.status = WorkerStatus.DRAFTING.value
        for lead_id in lead_ids:
            lead = db.get(Lead, lead_id)
            if not lead:
                continue
            generate_initial_sequence(db, campaign=campaign, lead=lead, require_approval=require_manual_approval)

        if require_manual_approval:
            worker.status = WorkerStatus.AWAITING_APPROVAL.value
            sent = 0
        else:
            worker.status = WorkerStatus.SENDING.value
            sent = send_approved_messages(db, workspace_id=worker.workspace_id, campaign_id=campaign.id)
            worker.status = WorkerStatus.MONITORING.value

        run.status = "completed"
        run.finished_at = datetime.now(UTC)
        run.output_json = {"leads_processed": lead_count, "emails_sent": sent}
        worker.status = WorkerStatus.MONITORING.value if sent else worker.status
        return run
