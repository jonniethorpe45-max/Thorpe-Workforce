from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import WorkerReview, WorkerTemplateTool, WorkerTool
from app.schemas.api import PublicWorkerDetailRead, PublicWorkerListItem
from app.services.worker_templates import get_worker_template_details, list_worker_templates

router = APIRouter(prefix="/public-workers", tags=["public_workers"])


@router.get("", response_model=list[PublicWorkerListItem])
def list_public_workers(
    category: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=120),
    pricing_type: str | None = Query(default=None),
    featured_only: bool = Query(default=False),
    sort_by: str | None = Query(default="featured"),
    db: Session = Depends(get_db),
):
    templates = list_worker_templates(
        db,
        workspace_id=None,
        include_workspace_templates=False,
        include_public_templates=True,
        include_global_non_public_templates=False,
        include_inactive=False,
    )
    items: list[PublicWorkerListItem] = []
    normalized_category = (category or "").strip().lower()
    normalized_search = (search or "").strip().lower()
    normalized_pricing = (pricing_type or "").strip().lower()
    for template in templates:
        if not template.slug:
            continue
        if normalized_category and (template.category or "").lower() != normalized_category:
            continue
        if normalized_pricing and (template.pricing_type or "").lower() != normalized_pricing:
            continue
        if featured_only and not template.is_featured:
            continue
        if normalized_search:
            haystack = " ".join(
                [
                    template.name or "",
                    template.display_name or "",
                    template.short_description or "",
                    template.description or "",
                    " ".join(template.tags_json or []),
                ]
            ).lower()
            if normalized_search not in haystack:
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
                is_featured=template.is_featured,
                featured_rank=template.featured_rank,
                tags_json=template.tags_json,
                created_at=template.created_at,
            )
        )
    normalized_sort = (sort_by or "featured").strip().lower()
    if normalized_sort == "new":
        items.sort(key=lambda item: item.created_at or datetime(1970, 1, 1, tzinfo=UTC), reverse=True)
    elif normalized_sort == "top":
        items.sort(key=lambda item: (item.install_count, item.rating_avg), reverse=True)
    elif normalized_sort == "rating":
        items.sort(key=lambda item: (item.rating_avg, item.rating_count), reverse=True)
    elif normalized_sort == "price_low":
        items.sort(key=lambda item: item.price_cents)
    elif normalized_sort == "price_high":
        items.sort(key=lambda item: item.price_cents, reverse=True)
    else:
        items.sort(
            key=lambda item: (
                0 if item.is_featured else 1,
                item.featured_rank,
                -item.install_count,
                -item.rating_avg,
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
    tools = (
        db.query(WorkerTool)
        .filter(
            WorkerTool.slug.in_(slugs) if slugs else False,
            WorkerTool.is_active.is_(True),
        )
        .all()
    )
    return PublicWorkerDetailRead(
        template=template,
        reviews=reviews,
        tools=tools,
        average_rating=template.rating_avg,
        installs=template.install_count,
    )
