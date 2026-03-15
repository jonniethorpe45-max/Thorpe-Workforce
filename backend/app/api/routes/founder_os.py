import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import FounderOSReportType, User
from app.schemas.api import (
    FounderOSAutomationCreate,
    FounderOSAutomationListResponse,
    FounderOSAutomationRead,
    FounderOSAutomationUpdate,
    FounderOSChainListResponse,
    FounderOSChainRead,
    FounderOSChainRunRequest,
    FounderOSChainRunResponse,
    FounderOSOverviewRead,
    FounderOSReportListResponse,
    FounderOSReportRead,
    WorkerChainStepExecutionRead,
)
from app.services.founder_os import (
    _automation_to_dict,
    _ensure_founder_user,
    create_founder_os_automation,
    founder_os_overview,
    get_founder_os_chain,
    get_founder_os_report,
    list_founder_os_automations,
    list_founder_os_chains,
    list_founder_os_reports,
    run_founder_os_chain,
    update_founder_os_automation,
)

router = APIRouter(prefix="/founder-os", tags=["founder_os"])


@router.get("/overview", response_model=FounderOSOverviewRead)
def get_founder_os_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_founder_user(current_user)
    payload = founder_os_overview(
        db,
        workspace_id=current_user.workspace_id,
        actor_user_id=current_user.id,
    )
    db.commit()
    return payload


@router.get("/chains", response_model=FounderOSChainListResponse)
def list_chains(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_founder_user(current_user)
    items = list_founder_os_chains(
        db,
        workspace_id=current_user.workspace_id,
        actor_user_id=current_user.id,
    )
    db.commit()
    return FounderOSChainListResponse(items=[FounderOSChainRead.model_validate(item) for item in items], total=len(items))


@router.get("/chains/{chain_id}", response_model=FounderOSChainRead)
def get_chain(
    chain_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_founder_user(current_user)
    item = get_founder_os_chain(
        db,
        workspace_id=current_user.workspace_id,
        chain_id=chain_id,
        actor_user_id=current_user.id,
    )
    db.commit()
    return FounderOSChainRead.model_validate(item)


@router.post("/chains/{chain_id}/run", response_model=FounderOSChainRunResponse)
def run_chain(
    chain_id: uuid.UUID,
    payload: FounderOSChainRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_founder_user(current_user)
    result, report = run_founder_os_chain(
        db,
        workspace_id=current_user.workspace_id,
        actor_user_id=current_user.id,
        chain_id=chain_id,
        payload=payload,
    )
    db.commit()
    return FounderOSChainRunResponse(
        success=result.success,
        chain_id=result.chain_id,
        chain_run_id=result.chain_run_id,
        status=result.status,
        report_id=report.id,
        total_steps_executed=result.total_steps_executed,
        executed_steps=[
            WorkerChainStepExecutionRead(
                step_order=item.step_order,
                status=item.status,
                run_id=item.run_id,
                worker_instance_id=item.worker_instance_id,
                worker_template_id=item.worker_template_id,
                summary=item.summary,
                error=item.error,
                next_step_order=item.next_step_order,
                skipped_reason=item.skipped_reason,
            )
            for item in result.executed_steps
        ],
    )


@router.get("/reports", response_model=FounderOSReportListResponse)
def list_reports(
    report_type: FounderOSReportType | None = Query(default=None),
    chain_id: uuid.UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_founder_user(current_user)
    items, total = list_founder_os_reports(
        db,
        workspace_id=current_user.workspace_id,
        report_type=report_type,
        chain_id=chain_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return FounderOSReportListResponse(items=[FounderOSReportRead.model_validate(item) for item in items], total=total)


@router.get("/reports/{report_id}", response_model=FounderOSReportRead)
def get_report(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_founder_user(current_user)
    report = get_founder_os_report(db, workspace_id=current_user.workspace_id, report_id=report_id)
    return FounderOSReportRead.model_validate(report)


@router.post("/automations", response_model=FounderOSAutomationRead)
def create_automation(
    payload: FounderOSAutomationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_founder_user(current_user)
    automation = create_founder_os_automation(
        db,
        workspace_id=current_user.workspace_id,
        actor_user_id=current_user.id,
        payload=payload,
    )
    db.commit()
    return FounderOSAutomationRead.model_validate(_automation_to_dict(db, automation))


@router.get("/automations", response_model=FounderOSAutomationListResponse)
def list_automations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_founder_user(current_user)
    items = list_founder_os_automations(db, workspace_id=current_user.workspace_id)
    payload = [FounderOSAutomationRead.model_validate(_automation_to_dict(db, item)) for item in items]
    return FounderOSAutomationListResponse(items=payload, total=len(payload))


@router.patch("/automations/{automation_id}", response_model=FounderOSAutomationRead)
def patch_automation(
    automation_id: uuid.UUID,
    payload: FounderOSAutomationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_founder_user(current_user)
    automation = update_founder_os_automation(
        db,
        workspace_id=current_user.workspace_id,
        actor_user_id=current_user.id,
        automation_id=automation_id,
        payload=payload,
    )
    db.commit()
    return FounderOSAutomationRead.model_validate(_automation_to_dict(db, automation))
