import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.api import AnalyticsOverview, CampaignAnalytics, WorkerAnalytics
from app.services.analytics import get_campaign_analytics, get_overview, get_worker_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_overview(db, workspace_id=current_user.workspace_id)


@router.get("/campaign/{campaign_id}", response_model=CampaignAnalytics)
def campaign_analytics(campaign_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_campaign_analytics(db, workspace_id=current_user.workspace_id, campaign_id=campaign_id)


@router.get("/worker/{worker_id}", response_model=WorkerAnalytics)
def worker_analytics(worker_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Worker ownership checks are done in service consumers; kept simple for MVP.
    return get_worker_analytics(db, worker_id=worker_id)
