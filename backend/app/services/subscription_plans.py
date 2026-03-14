import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import SubscriptionPlan


@dataclass(frozen=True)
class SubscriptionPlanSeed:
    code: str
    name: str
    description: str
    monthly_price_cents: int
    annual_price_cents: int | None
    max_worker_drafts: int | None
    max_published_workers: int | None
    max_worker_installs_per_workspace: int | None
    max_worker_runs_per_month: int | None
    allow_worker_builder: bool
    allow_marketplace_publishing: bool
    allow_private_workers: bool
    allow_public_workers: bool
    allow_marketplace_install: bool
    allow_team_features: bool
    is_active: bool


DEFAULT_PLAN_SEEDS: tuple[SubscriptionPlanSeed, ...] = (
    SubscriptionPlanSeed(
        code="free",
        name="Free",
        description="Explore Thorpe Workforce with limited capacity.",
        monthly_price_cents=0,
        annual_price_cents=None,
        max_worker_drafts=2,
        max_published_workers=1,
        max_worker_installs_per_workspace=3,
        max_worker_runs_per_month=50,
        allow_worker_builder=True,
        allow_marketplace_publishing=False,
        allow_private_workers=True,
        allow_public_workers=False,
        allow_marketplace_install=True,
        allow_team_features=False,
        is_active=True,
    ),
    SubscriptionPlanSeed(
        code="pro",
        name="Pro",
        description="Scale an AI workforce with higher limits and private/public workers.",
        monthly_price_cents=4900,
        annual_price_cents=49000,
        max_worker_drafts=25,
        max_published_workers=10,
        max_worker_installs_per_workspace=50,
        max_worker_runs_per_month=3000,
        allow_worker_builder=True,
        allow_marketplace_publishing=False,
        allow_private_workers=True,
        allow_public_workers=True,
        allow_marketplace_install=True,
        allow_team_features=False,
        is_active=True,
    ),
    SubscriptionPlanSeed(
        code="creator",
        name="Creator",
        description="Publish, monetize, and operate marketplace-ready workers.",
        monthly_price_cents=9900,
        annual_price_cents=99000,
        max_worker_drafts=200,
        max_published_workers=100,
        max_worker_installs_per_workspace=200,
        max_worker_runs_per_month=15000,
        allow_worker_builder=True,
        allow_marketplace_publishing=True,
        allow_private_workers=True,
        allow_public_workers=True,
        allow_marketplace_install=True,
        allow_team_features=True,
        is_active=True,
    ),
    SubscriptionPlanSeed(
        code="enterprise",
        name="Enterprise",
        description="Unlimited operations, governance, and advanced support.",
        monthly_price_cents=29900,
        annual_price_cents=None,
        max_worker_drafts=None,
        max_published_workers=None,
        max_worker_installs_per_workspace=None,
        max_worker_runs_per_month=None,
        allow_worker_builder=True,
        allow_marketplace_publishing=True,
        allow_private_workers=True,
        allow_public_workers=True,
        allow_marketplace_install=True,
        allow_team_features=True,
        is_active=True,
    ),
    # Legacy compatibility plan to preserve existing workspace behavior.
    SubscriptionPlanSeed(
        code="starter",
        name="Starter (Legacy)",
        description="Legacy plan retained for backwards compatibility.",
        monthly_price_cents=0,
        annual_price_cents=None,
        max_worker_drafts=None,
        max_published_workers=None,
        max_worker_installs_per_workspace=None,
        max_worker_runs_per_month=None,
        allow_worker_builder=True,
        allow_marketplace_publishing=True,
        allow_private_workers=True,
        allow_public_workers=True,
        allow_marketplace_install=True,
        allow_team_features=False,
        is_active=False,
    ),
)


def ensure_default_subscription_plans(db: Session) -> list[SubscriptionPlan]:
    existing = {item.code: item for item in db.query(SubscriptionPlan).all()}
    plans: list[SubscriptionPlan] = []
    for seed in DEFAULT_PLAN_SEEDS:
        plan = existing.get(seed.code)
        if not plan:
            plan = SubscriptionPlan(
                id=uuid.uuid4(),
                code=seed.code,
                name=seed.name,
                description=seed.description,
            )
            db.add(plan)
        plan.name = seed.name
        plan.description = seed.description
        plan.monthly_price_cents = int(seed.monthly_price_cents)
        plan.annual_price_cents = int(seed.annual_price_cents) if seed.annual_price_cents is not None else None
        if seed.code == "pro":
            plan.stripe_price_id_monthly = settings.stripe_price_id_pro_monthly or plan.stripe_price_id_monthly
            plan.stripe_price_id_annual = settings.stripe_price_id_pro_annual or plan.stripe_price_id_annual
        elif seed.code == "creator":
            plan.stripe_price_id_monthly = settings.stripe_price_id_creator_monthly or plan.stripe_price_id_monthly
            plan.stripe_price_id_annual = settings.stripe_price_id_creator_annual or plan.stripe_price_id_annual
        elif seed.code == "enterprise":
            plan.stripe_price_id_monthly = settings.stripe_price_id_enterprise_monthly or plan.stripe_price_id_monthly
        plan.max_worker_drafts = seed.max_worker_drafts
        plan.max_published_workers = seed.max_published_workers
        plan.max_worker_installs_per_workspace = seed.max_worker_installs_per_workspace
        plan.max_worker_runs_per_month = seed.max_worker_runs_per_month
        plan.allow_worker_builder = bool(seed.allow_worker_builder)
        plan.allow_marketplace_publishing = bool(seed.allow_marketplace_publishing)
        plan.allow_private_workers = bool(seed.allow_private_workers)
        plan.allow_public_workers = bool(seed.allow_public_workers)
        plan.allow_marketplace_install = bool(seed.allow_marketplace_install)
        plan.allow_team_features = bool(seed.allow_team_features)
        plan.is_active = bool(seed.is_active)
        plans.append(plan)
    db.flush()
    return plans


def get_plan_by_code(db: Session, code: str, *, include_inactive: bool = True) -> SubscriptionPlan | None:
    query = db.query(SubscriptionPlan).filter(SubscriptionPlan.code == (code or "").strip().lower())
    if not include_inactive:
        query = query.filter(SubscriptionPlan.is_active.is_(True))
    return query.first()
