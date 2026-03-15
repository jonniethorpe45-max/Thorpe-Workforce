from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.api import (
    OnboardingRecommendationItem,
    OnboardingRecommendationResponse,
    OnboardingStateRead,
    OnboardingStateUpdate,
)
from app.services.audit import log_audit_event
from app.services.onboarding import build_recommendations, get_or_create_onboarding_state, update_onboarding_state

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/state", response_model=OnboardingStateRead)
def onboarding_state(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    state = get_or_create_onboarding_state(db, user=current_user)
    db.commit()
    db.refresh(state)
    return state


@router.patch("/state", response_model=OnboardingStateRead)
def patch_onboarding_state(
    payload: OnboardingStateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    state = get_or_create_onboarding_state(db, user=current_user)
    updated = update_onboarding_state(
        db,
        state=state,
        current_step=payload.current_step,
        goal_category=payload.goal_category.value if payload.goal_category else None,
        selected_paths=payload.selected_paths_json,
        complete_step=payload.complete_step,
        is_completed=payload.is_completed,
        is_skipped=payload.is_skipped,
    )
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="onboarding_state_updated",
        payload=payload.model_dump(exclude_none=True),
    )
    if payload.is_completed:
        log_audit_event(
            db,
            workspace_id=current_user.workspace_id,
            actor_type="user",
            actor_id=str(current_user.id),
            event_name="onboarding_completed",
            payload={"current_step": updated.current_step, "goal_category": updated.goal_category},
        )
    db.commit()
    db.refresh(updated)
    return updated


@router.get("/recommendations", response_model=OnboardingRecommendationResponse)
def onboarding_recommendations(
    goal_category: str = Query(..., min_length=3, max_length=40),
    limit: int = Query(default=5, ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    normalized_goal = goal_category.strip().lower()
    templates = build_recommendations(
        db,
        user=current_user,
        goal_category=normalized_goal,
        limit=limit,
    )
    return OnboardingRecommendationResponse(
        goal_category=normalized_goal,
        templates=[
            OnboardingRecommendationItem(
                id=item.id,
                slug=item.slug or "",
                name=item.display_name or item.name,
                short_description=item.short_description,
                category=item.category,
                pricing_type=item.pricing_type,
                price_cents=item.price_cents,
                currency=item.currency,
                is_featured=item.is_featured,
                featured_rank=item.featured_rank,
                install_count=item.install_count,
            )
            for item in templates
            if item.slug
        ],
    )
