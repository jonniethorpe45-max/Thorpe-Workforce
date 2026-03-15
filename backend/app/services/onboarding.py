import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import OnboardingGoal, User, UserOnboardingState, WorkerTemplate

ONBOARDING_DEFAULT_STEPS = ["welcome", "workspace_setup", "goal_selection", "recommendations", "first_success"]
GOAL_CATEGORY_MAP: dict[str, set[str]] = {
    OnboardingGoal.REAL_ESTATE.value: {"real_estate"},
    OnboardingGoal.MARKETING.value: {"marketing"},
    OnboardingGoal.SALES.value: {"sales", "prospecting"},
    OnboardingGoal.ECOMMERCE.value: {"ecommerce", "marketing"},
    OnboardingGoal.RESEARCH.value: {"research", "prospecting"},
    OnboardingGoal.OPERATIONS.value: {"operations", "automation", "meetings"},
    OnboardingGoal.CUSTOM.value: {"custom", "general"},
}


def _normalize_goal(goal_category: str | None) -> str | None:
    if goal_category is None:
        return None
    normalized = goal_category.strip().lower()
    allowed = {item.value for item in OnboardingGoal}
    if normalized not in allowed:
        raise HTTPException(status_code=400, detail="Invalid onboarding goal_category")
    return normalized


def get_or_create_onboarding_state(db: Session, *, user: User) -> UserOnboardingState:
    state = db.query(UserOnboardingState).filter(UserOnboardingState.user_id == user.id).first()
    if state:
        return state
    state = UserOnboardingState(
        user_id=user.id,
        workspace_id=user.workspace_id,
        current_step="welcome",
        selected_paths_json=[],
        completed_steps_json=[],
        recommended_template_slugs=[],
        is_completed=False,
        is_skipped=False,
    )
    db.add(state)
    db.flush()
    return state


def _recommended_templates_for_goal(
    db: Session,
    *,
    goal_category: str,
    workspace_id: uuid.UUID,
    limit: int = 5,
) -> list[WorkerTemplate]:
    categories = GOAL_CATEGORY_MAP.get(goal_category, {goal_category})
    query = (
        db.query(WorkerTemplate)
        .filter(
            WorkerTemplate.is_active.is_(True),
            WorkerTemplate.status == "active",
            WorkerTemplate.slug.is_not(None),
            or_(
                WorkerTemplate.workspace_id == workspace_id,
                WorkerTemplate.visibility.in_(("public", "marketplace")),
                WorkerTemplate.is_public.is_(True),
            ),
            WorkerTemplate.category.in_(tuple(categories)),
        )
        .order_by(
            WorkerTemplate.is_featured.desc(),
            WorkerTemplate.featured_rank.asc(),
            WorkerTemplate.install_count.desc(),
            WorkerTemplate.created_at.desc(),
        )
        .limit(max(limit, 1))
    )
    items = query.all()
    if items:
        return items
    return (
        db.query(WorkerTemplate)
        .filter(
            WorkerTemplate.is_active.is_(True),
            WorkerTemplate.status == "active",
            WorkerTemplate.slug.is_not(None),
            or_(
                WorkerTemplate.workspace_id == workspace_id,
                WorkerTemplate.visibility.in_(("public", "marketplace")),
                WorkerTemplate.is_public.is_(True),
            ),
        )
        .order_by(
            WorkerTemplate.is_featured.desc(),
            WorkerTemplate.featured_rank.asc(),
            WorkerTemplate.install_count.desc(),
            WorkerTemplate.created_at.desc(),
        )
        .limit(max(limit, 1))
        .all()
    )


def update_onboarding_state(
    db: Session,
    *,
    state: UserOnboardingState,
    current_step: str | None = None,
    goal_category: str | None = None,
    selected_paths: list[str] | None = None,
    complete_step: str | None = None,
    is_completed: bool | None = None,
    is_skipped: bool | None = None,
) -> UserOnboardingState:
    if current_step:
        state.current_step = current_step.strip().lower()
    normalized_goal = _normalize_goal(goal_category)
    if normalized_goal:
        state.goal_category = normalized_goal
        recommended = _recommended_templates_for_goal(
            db,
            goal_category=normalized_goal,
            workspace_id=state.workspace_id,
            limit=5,
        )
        state.recommended_template_slugs = [item.slug for item in recommended if item.slug]
    if selected_paths is not None:
        state.selected_paths_json = [item.strip().lower() for item in selected_paths if item.strip()]
    if complete_step:
        completed = set(state.completed_steps_json or [])
        completed.add(complete_step.strip().lower())
        state.completed_steps_json = sorted(completed)
    if is_completed is not None:
        state.is_completed = bool(is_completed)
        if state.is_completed:
            state.last_completed_at = datetime.now(UTC)
    if is_skipped is not None:
        state.is_skipped = bool(is_skipped)
    db.flush()
    return state


def build_recommendations(
    db: Session,
    *,
    user: User,
    goal_category: str,
    limit: int = 5,
) -> list[WorkerTemplate]:
    normalized_goal = _normalize_goal(goal_category)
    if not normalized_goal:
        raise HTTPException(status_code=400, detail="goal_category is required")
    return _recommended_templates_for_goal(
        db,
        goal_category=normalized_goal,
        workspace_id=user.workspace_id,
        limit=limit,
    )
