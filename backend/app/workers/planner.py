from sqlalchemy.orm import Session

from app.models import Campaign, Lead, LeadStatus, Worker
from app.services.email_safety import is_lead_send_eligible


class WorkerPlanner:
    def build_execution_plan(self, db: Session, worker: Worker, campaign: Campaign) -> dict:
        candidate_leads = (
            db.query(Lead)
            .filter(
                Lead.campaign_id == campaign.id,
                Lead.lead_status.in_([LeadStatus.NEW.value, LeadStatus.READY_FOR_OUTREACH.value]),
            )
            .order_by(Lead.created_at.asc())
            .limit(worker.send_limit_per_day * 3)
            .all()
        )
        lead_ids: list[str] = []
        skipped: list[dict[str, str]] = []
        for lead in candidate_leads:
            eligible, reason = is_lead_send_eligible(
                db=db,
                workspace_id=worker.workspace_id,
                campaign_id=campaign.id,
                lead=lead,
                sequence_step=1,
            )
            if eligible:
                lead_ids.append(str(lead.id))
            else:
                skipped.append({"lead_id": str(lead.id), "reason": reason})
            if len(lead_ids) >= worker.send_limit_per_day:
                break
        return {
            "worker_id": str(worker.id),
            "campaign_id": str(campaign.id),
            "lead_ids": lead_ids,
            "skipped_leads": skipped,
            "send_limit": worker.send_limit_per_day,
        }
