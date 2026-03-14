import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User, WorkerInstance, WorkerSubscription, WorkerTemplateVisibility
from app.schemas.api import MarketplaceInstallResponse, MarketplaceListingRead, WorkerTemplateInstallRequest
from app.services.worker_templates import get_worker_template_details, install_worker_template, list_worker_templates

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


@router.get("/templates", response_model=list[MarketplaceListingRead])
def list_marketplace_templates(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    templates = list_worker_templates(
        db,
        workspace_id=current_user.workspace_id,
        include_workspace_templates=False,
        include_public_templates=True,
        include_global_non_public_templates=False,
        marketplace_only=True,
    )
    template_ids = [item.id for item in templates]
    installed_template_ids = {
        row[0]
        for row in db.query(WorkerInstance.template_id)
        .filter(
            WorkerInstance.workspace_id == current_user.workspace_id,
            WorkerInstance.template_id.in_(template_ids) if template_ids else False,
        )
        .all()
    }
    subscriptions = (
        db.query(WorkerSubscription)
        .filter(
            WorkerSubscription.workspace_id == current_user.workspace_id,
            WorkerSubscription.worker_template_id.in_(template_ids) if template_ids else False,
            WorkerSubscription.is_active.is_(True),
        )
        .all()
    )
    subscription_by_template = {item.worker_template_id: item for item in subscriptions}
    return [
        MarketplaceListingRead(
            template=template,
            is_installed=template.id in installed_template_ids,
            subscription=subscription_by_template.get(template.id),
        )
        for template in templates
    ]


@router.post("/templates/{template_id}/install", response_model=MarketplaceInstallResponse)
def install_marketplace_template(
    template_id: uuid.UUID,
    payload: WorkerTemplateInstallRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = get_worker_template_details(
        db,
        template_id=template_id,
        workspace_id=current_user.workspace_id,
        include_public=True,
        include_global_non_public=False,
    )
    if not template.is_marketplace_listed and template.visibility != WorkerTemplateVisibility.MARKETPLACE.value:
        raise HTTPException(status_code=404, detail="Marketplace template not found")
    install_result = install_worker_template(
        db,
        template=template,
        workspace_id=current_user.workspace_id,
        installer_user_id=current_user.id,
        instance_name=payload.instance_name,
        runtime_config_overrides=payload.runtime_config_overrides,
        schedule_expression=payload.schedule_expression,
        memory_scope=payload.memory_scope,
    )
    if install_result.subscription is None:
        raise HTTPException(status_code=400, detail="Marketplace template requires a subscription record")
    db.commit()
    db.refresh(install_result.subscription)
    return MarketplaceInstallResponse(
        success=True,
        worker_template_id=template.id,
        subscription=install_result.subscription,
        message="Template installed successfully",
    )
