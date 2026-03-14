from sqlalchemy.orm import Session

from app.models import Campaign, Lead, LeadStatus, Worker


class WorkerPlanner:
    def build_execution_plan(self, db: Session, worker: Worker, campaign: Campaign) -> dict:
        leads = (
            db.query(Lead)
            .filter(
                Lead.campaign_id == campaign.id,
                Lead.lead_status.in_([LeadStatus.NEW.value, LeadStatus.READY_FOR_OUTREACH.value]),
            )
            .limit(worker.send_limit_per_day)
            .all()
        )
        return {
            "worker_id": str(worker.id),
            "campaign_id": str(campaign.id),
            "lead_ids": [str(lead.id) for lead in leads],
            "send_limit": worker.send_limit_per_day,
        }
