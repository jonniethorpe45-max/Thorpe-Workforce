import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User, Worker
from app.schemas.api import (
    AnalyticsOverview,
    CampaignAnalytics,
    WorkerAnalytics,
    WorkspaceActivityRead,
    WorkspaceAnalyticsSummaryRead,
    WorkspaceUsageHistoryPointRead,
)
from app.services.analytics import get_campaign_analytics, get_overview, get_worker_analytics
from app.services.platform_analytics import workspace_activity, workspace_summary, workspace_usage_history

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_overview(db, workspace_id=current_user.workspace_id)


@router.get("/campaign/{campaign_id}", response_model=CampaignAnalytics)
def campaign_analytics(campaign_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_campaign_analytics(db, workspace_id=current_user.workspace_id, campaign_id=campaign_id)


@router.get("/worker/{worker_id}", response_model=WorkerAnalytics)
def worker_analytics(worker_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    worker = db.get(Worker, worker_id)
    if not worker or worker.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Worker not found")
    return get_worker_analytics(db, worker_id=worker_id)


@router.get("/workspace/summary", response_model=WorkspaceAnalyticsSummaryRead)
def workspace_analytics_summary(
    range: str | None = Query(default="30d"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return workspace_summary(
        db,
        workspace_id=current_user.workspace_id,
        range_value=range,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/workspace/activity", response_model=list[WorkspaceActivityRead])
def workspace_analytics_activity(
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return workspace_activity(db, workspace_id=current_user.workspace_id, limit=limit)


@router.get("/workspace/usage-history", response_model=list[WorkspaceUsageHistoryPointRead])
def workspace_analytics_usage_history(
    range: str | None = Query(default="30d"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return workspace_usage_history(
        db,
        workspace_id=current_user.workspace_id,
        range_value=range,
        start_date=start_date,
        end_date=end_date,
    )
