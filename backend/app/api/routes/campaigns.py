import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import ApprovalStatus, Campaign, EmailSequence, GeneratedMessage, SentEmail, User, Worker
from app.schemas.api import CampaignCreate, CampaignRead, CampaignUpdate
from app.services.audit import log_audit_event
from app.services.message_generator import send_approved_messages
from app.services.worker_service import run_worker_for_campaign

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post("", response_model=CampaignRead)
def create_campaign(payload: CampaignCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.worker_id:
        worker = db.get(Worker, payload.worker_id)
        if not worker or worker.workspace_id != current_user.workspace_id:
            raise HTTPException(status_code=404, detail="Worker not found")
    campaign = Campaign(
        workspace_id=current_user.workspace_id,
        worker_id=payload.worker_id,
        name=payload.name,
        target_industry=payload.target_industry,
        target_roles=payload.target_roles,
        target_locations=payload.target_locations,
        company_size_min=payload.company_size_min,
        company_size_max=payload.company_size_max,
        cta_text=payload.cta_text,
        status="draft",
    )
    db.add(campaign)
    db.flush()
    sequence_defaults = [
        ("Initial outreach", 1, payload.scheduling_settings.get("step_1_delay_days", 0)),
        ("Follow-up 1", 2, payload.scheduling_settings.get("step_2_delay_days", 3)),
        ("Follow-up 2", 3, payload.scheduling_settings.get("step_3_delay_days", 7)),
        ("Follow-up 3", 4, payload.scheduling_settings.get("step_4_delay_days", 12)),
    ]
    for name, step, delay in sequence_defaults:
        db.add(
            EmailSequence(
                campaign_id=campaign.id,
                sequence_name=name,
                step_order=step,
                subject_template=f"{name} subject",
                body_template=f"{name} body",
                delay_days=int(delay),
            )
        )
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="campaign_created",
        payload={"campaign_name": campaign.name, "exclusions": payload.exclusions},
    )
    db.commit()
    db.refresh(campaign)
    return campaign


@router.get("", response_model=list[CampaignRead])
def list_campaigns(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Campaign).filter(Campaign.workspace_id == current_user.workspace_id).order_by(Campaign.created_at.desc()).all()
    )


@router.get("/{campaign_id}", response_model=CampaignRead)
def get_campaign(campaign_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    campaign = db.get(Campaign, campaign_id)
    if not campaign or campaign.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.patch("/{campaign_id}", response_model=CampaignRead)
def update_campaign(
    campaign_id: uuid.UUID,
    payload: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    campaign = db.get(Campaign, campaign_id)
    if not campaign or campaign.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(campaign, field, value)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/launch")
def launch_campaign(campaign_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    campaign = db.get(Campaign, campaign_id)
    if not campaign or campaign.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if not campaign.worker_id:
        raise HTTPException(status_code=400, detail="Campaign requires an assigned worker")
    worker = db.get(Worker, campaign.worker_id)
    if not worker or worker.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Worker not found")

    approved_messages_exist = (
        db.query(GeneratedMessage)
        .filter(
            GeneratedMessage.campaign_id == campaign.id,
            GeneratedMessage.approval_status == ApprovalStatus.APPROVED.value,
        )
        .count()
        > 0
    )
    if approved_messages_exist:
        sent = send_approved_messages(db, workspace_id=current_user.workspace_id, campaign_id=campaign.id)
        log_audit_event(
            db,
            workspace_id=current_user.workspace_id,
            actor_type="user",
            actor_id=str(current_user.id),
            event_name="campaign_sent_approved_messages",
            payload={"campaign_id": str(campaign.id), "sent_count": sent},
        )
        db.commit()
        return {"success": True, "sent_count": sent, "manual_approval_required": False}

    prior_sent_count = db.query(SentEmail).filter(SentEmail.workspace_id == current_user.workspace_id).count()
    require_manual_approval = prior_sent_count == 0
    campaign.status = "active"
    run = run_worker_for_campaign(db, worker=worker, campaign=campaign, require_manual_approval=require_manual_approval)
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="campaign_launched",
        payload={"campaign_id": str(campaign.id), "manual_approval_required": require_manual_approval},
    )
    db.commit()
    return {"success": True, "run_id": str(run.id), "manual_approval_required": require_manual_approval}


@router.post("/{campaign_id}/pause")
def pause_campaign(campaign_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    campaign = db.get(Campaign, campaign_id)
    if not campaign or campaign.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.status = "paused"
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="campaign_paused",
        payload={"campaign_id": str(campaign.id)},
    )
    db.commit()
    return {"success": True}
