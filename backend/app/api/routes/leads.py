import json
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Lead, User
from app.schemas.api import LeadCreate, LeadRead, LeadUpdate
from app.services.audit import log_audit_event
from app.services.lead_service import create_single_lead, import_leads_from_rows, parse_csv_bytes

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=list[LeadRead])
def list_leads(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Lead).filter(Lead.workspace_id == current_user.workspace_id).order_by(Lead.created_at.desc()).all()


@router.post("/import")
async def import_leads(
    file: UploadFile | None = File(default=None),
    json_rows: str | None = Form(default=None),
    campaign_id: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows: list[dict] = []
    if file:
        content = await file.read()
        rows = parse_csv_bytes(content)
    elif json_rows:
        rows = json.loads(json_rows)
    else:
        raise HTTPException(status_code=400, detail="Provide CSV file or json_rows payload")
    result = import_leads_from_rows(
        db,
        workspace_id=current_user.workspace_id,
        rows=rows,
        campaign_id=uuid.UUID(campaign_id) if campaign_id else None,
    )
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="leads_imported",
        payload=result,
    )
    db.commit()
    return result


@router.post("", response_model=LeadRead)
def create_lead(payload: LeadCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lead = create_single_lead(db, workspace_id=current_user.workspace_id, payload=payload)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead or lead.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}", response_model=LeadRead)
def update_lead(
    lead_id: uuid.UUID,
    payload: LeadUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.get(Lead, lead_id)
    if not lead or lead.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Lead not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(lead, field, value)
    db.commit()
    db.refresh(lead)
    return lead
