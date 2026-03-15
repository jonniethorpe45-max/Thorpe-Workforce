import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.api import (
    CreatorActivityItemRead,
    CreatorDashboardSummaryRead,
    CreatorPayoutsSummaryRead,
    CreatorWorkerAnalyticsRead,
    CreatorWorkerSummaryRead,
)
from app.services.platform_analytics import (
    creator_activity,
    creator_dashboard_summary,
    creator_payouts_summary,
    creator_worker_analytics,
    creator_workers_list,
)

router = APIRouter(prefix="/creator", tags=["creator_dashboard"])


@router.get("/dashboard/summary", response_model=CreatorDashboardSummaryRead)
def creator_summary(
    range: str | None = Query(default="30d"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return creator_dashboard_summary(
        db,
        creator_user_id=current_user.id,
        range_value=range,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/workers", response_model=list[CreatorWorkerSummaryRead])
def creator_workers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return creator_workers_list(db, creator_user_id=current_user.id)


@router.get("/workers/{worker_id}/analytics", response_model=CreatorWorkerAnalyticsRead)
def creator_worker_detail_analytics(
    worker_id: uuid.UUID,
    range: str | None = Query(default="30d"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return creator_worker_analytics(
        db,
        creator_user_id=current_user.id,
        worker_template_id=worker_id,
        range_value=range,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/payouts/summary", response_model=CreatorPayoutsSummaryRead)
def creator_payout_summary(
    range: str | None = Query(default="30d"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return creator_payouts_summary(
        db,
        creator_user_id=current_user.id,
        range_value=range,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/activity", response_model=list[CreatorActivityItemRead])
def creator_recent_activity(
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return creator_activity(db, creator_user_id=current_user.id, limit=limit)
