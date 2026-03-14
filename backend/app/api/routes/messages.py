import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import ApprovalStatus, Campaign, GeneratedMessage, Lead, User, Worker
from app.schemas.api import MessageRead
from app.services.message_generator import regenerate_message

router = APIRouter(tags=["messages"])


@router.get("/campaigns/{campaign_id}/messages", response_model=list[MessageRead])
def list_campaign_messages(campaign_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    campaign = db.get(Campaign, campaign_id)
    if not campaign or campaign.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return (
        db.query(GeneratedMessage)
        .filter(GeneratedMessage.campaign_id == campaign_id)
        .order_by(GeneratedMessage.lead_id.asc(), GeneratedMessage.sequence_step.asc())
        .all()
    )


@router.post("/messages/{message_id}/approve")
def approve_message(message_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    message = db.get(GeneratedMessage, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    campaign = db.get(Campaign, message.campaign_id)
    if not campaign or campaign.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    message.approval_status = ApprovalStatus.APPROVED.value
    db.commit()
    return {"success": True}


@router.post("/messages/{message_id}/reject")
def reject_message(message_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    message = db.get(GeneratedMessage, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    campaign = db.get(Campaign, message.campaign_id)
    if not campaign or campaign.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    message.approval_status = ApprovalStatus.REJECTED.value
    db.commit()
    return {"success": True}


@router.post("/messages/{message_id}/regenerate", response_model=MessageRead)
def regenerate(message_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    message = db.get(GeneratedMessage, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    campaign = db.get(Campaign, message.campaign_id)
    lead = db.get(Lead, message.lead_id)
    if not campaign or campaign.workspace_id != current_user.workspace_id or not lead:
        raise HTTPException(status_code=404, detail="Campaign or lead not found")
    worker_type = "ai_sales_worker"
    if campaign.worker_id:
        worker = db.get(Worker, campaign.worker_id)
        if worker:
            worker_type = worker.worker_type
    regenerate_message(db, message=message, campaign=campaign, lead=lead, worker_type=worker_type)
    db.commit()
    db.refresh(message)
    return message
