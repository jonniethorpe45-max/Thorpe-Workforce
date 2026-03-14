from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import WorkerReview, WorkerTemplateTool, WorkerTool
from app.schemas.api import PublicWorkerDetailRead, PublicWorkerListItem
from app.services.worker_templates import get_worker_template_details, list_worker_templates

router = APIRouter(prefix="/public-workers", tags=["public_workers"])


@router.get("", response_model=list[PublicWorkerListItem])
def list_public_workers(db: Session = Depends(get_db)):
    templates = list_worker_templates(
        db,
        workspace_id=None,
        include_workspace_templates=False,
        include_public_templates=True,
        include_global_non_public_templates=False,
        include_inactive=False,
    )
    items: list[PublicWorkerListItem] = []
    for template in templates:
        if not template.slug:
            continue
        items.append(
            PublicWorkerListItem(
                id=template.id,
                slug=template.slug,
                name=template.name,
                short_description=template.short_description,
                category=template.category,
                pricing_type=template.pricing_type,
                price_cents=template.price_cents,
                currency=template.currency,
                rating_avg=template.rating_avg,
                rating_count=template.rating_count,
                install_count=template.install_count,
                tags_json=template.tags_json,
            )
        )
    return items


@router.get("/{slug}", response_model=PublicWorkerDetailRead)
def get_public_worker(slug: str, db: Session = Depends(get_db)):
    template = get_worker_template_details(
        db,
        slug=slug,
        workspace_id=None,
        include_public=True,
        include_global_non_public=False,
    )
    if not template.slug:
        raise HTTPException(status_code=404, detail="Public worker not found")

    reviews = (
        db.query(WorkerReview)
        .filter(WorkerReview.worker_template_id == template.id)
        .order_by(WorkerReview.created_at.desc())
        .limit(50)
        .all()
    )
    configured_tool_slugs = [str(item).strip() for item in (template.tools_json or []) if str(item).strip()]
    linked_tool_slugs = [
        row[0]
        for row in db.query(WorkerTool.slug)
        .join(WorkerTemplateTool, WorkerTemplateTool.worker_tool_id == WorkerTool.id)
        .filter(WorkerTemplateTool.worker_template_id == template.id, WorkerTool.is_active.is_(True))
        .all()
    ]
    slugs = sorted(set(configured_tool_slugs + linked_tool_slugs))
    tools = db.query(WorkerTool).filter(WorkerTool.slug.in_(slugs) if slugs else False).all()
    return PublicWorkerDetailRead(
        template=template,
        reviews=reviews,
        tools=tools,
        average_rating=template.rating_avg,
        installs=template.install_count,
    )
