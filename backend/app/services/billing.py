from dataclasses import dataclass

from app.core.config import settings
from app.models import WorkerPricingType, WorkerTemplate


@dataclass(frozen=True)
class BillingResult:
    billing_status: str
    is_captured: bool
    external_reference: str | None = None
    message: str | None = None


class BillingService:
    def process_marketplace_subscription(self, template: WorkerTemplate) -> BillingResult:
        raise NotImplementedError


class PlaceholderBillingService(BillingService):
    def process_marketplace_subscription(self, template: WorkerTemplate) -> BillingResult:
        if template.pricing_type in {WorkerPricingType.FREE.value, WorkerPricingType.INTERNAL.value} or template.price_cents <= 0:
            return BillingResult(
                billing_status="active",
                is_captured=True,
                message="No payment required for this template.",
            )
        return BillingResult(
            billing_status="pending_payment",
            is_captured=False,
            message="Billing provider is not configured. Payment capture is pending.",
        )


def get_billing_service() -> BillingService:
    # Stripe integration can be added behind this abstraction.
    _ = settings.billing_provider
    return PlaceholderBillingService()
