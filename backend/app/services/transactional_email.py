from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import secrets

from app.core.config import settings
from app.integrations.email.base import SendEmailInput
from app.integrations.email.factory import get_email_provider


@dataclass(frozen=True)
class TransactionalEmailTemplate:
    subject: str
    text_body: str
    html_body: str


def _app_url(path: str) -> str:
    base = settings.app_base_url.rstrip("/")
    normalized = path if path.startswith("/") else f"/{path}"
    return f"{base}{normalized}"


def render_template(template_key: str, *, recipient_name: str | None = None, context: dict | None = None) -> TransactionalEmailTemplate:
    ctx = context or {}
    name = (recipient_name or "there").strip()
    dashboard_url = _app_url("/app")
    pricing_url = _app_url("/pricing")
    settings_url = _app_url("/app/settings/billing")
    support_email = settings.support_email
    worker_name = str(ctx.get("worker_name") or "your worker")
    amount_text = str(ctx.get("amount_text") or "$0.00")
    reset_url = str(ctx.get("reset_url") or _app_url("/login"))

    if template_key == "welcome":
        subject = "Welcome to Thorpe Workforce"
        text = (
            f"Hi {name},\n\nWelcome to Thorpe Workforce. You can now deploy AI workers, run missions, and scale operations.\n"
            f"Open your dashboard: {dashboard_url}\n\nNeed help? {support_email}"
        )
        html = (
            f"<h2>Welcome to Thorpe Workforce</h2><p>Hi {name},</p>"
            f"<p>You can now deploy AI workers, run missions, and scale operations.</p>"
            f"<p><a href='{dashboard_url}'>Open your dashboard</a></p><p>Need help? {support_email}</p>"
        )
        return TransactionalEmailTemplate(subject=subject, text_body=text, html_body=html)

    if template_key == "workspace_ready":
        subject = "Your workspace is ready"
        text = (
            f"Hi {name},\n\nYour workspace is ready. Start with the onboarding flow to install your first worker.\n"
            f"Continue setup: {_app_url('/app/onboarding')}\n\nSupport: {support_email}"
        )
        html = (
            f"<h2>Your workspace is ready</h2><p>Hi {name},</p>"
            f"<p>Start with onboarding to install your first worker.</p>"
            f"<p><a href='{_app_url('/app/onboarding')}'>Continue setup</a></p><p>Support: {support_email}</p>"
        )
        return TransactionalEmailTemplate(subject=subject, text_body=text, html_body=html)

    if template_key == "subscription_active":
        subject = "Your subscription is active"
        text = (
            f"Hi {name},\n\nYour Thorpe Workforce subscription is active.\n"
            f"Manage billing here: {settings_url}\nExplore plans: {pricing_url}"
        )
        html = (
            f"<h2>Your subscription is active</h2><p>Hi {name},</p>"
            f"<p>Your Thorpe Workforce subscription is active.</p>"
            f"<p><a href='{settings_url}'>Manage billing</a> · <a href='{pricing_url}'>View plans</a></p>"
        )
        return TransactionalEmailTemplate(subject=subject, text_body=text, html_body=html)

    if template_key == "worker_published":
        subject = "Your worker has been published"
        text = (
            f"Hi {name},\n\nGreat news — {worker_name} has been published.\n"
            f"You can monitor performance in your creator dashboard: {_app_url('/app/creator')}"
        )
        html = (
            f"<h2>Your worker has been published</h2><p>Hi {name},</p>"
            f"<p><strong>{worker_name}</strong> is now published.</p>"
            f"<p><a href='{_app_url('/app/creator')}'>Open creator dashboard</a></p>"
        )
        return TransactionalEmailTemplate(subject=subject, text_body=text, html_body=html)

    if template_key == "purchase_confirmed":
        subject = "Your purchase is confirmed"
        text = (
            f"Hi {name},\n\nYour purchase is confirmed ({amount_text}).\n"
            f"You can install and run your worker from the marketplace: {_app_url('/app/marketplace')}"
        )
        html = (
            f"<h2>Your purchase is confirmed</h2><p>Hi {name},</p>"
            f"<p>Your purchase is confirmed (<strong>{amount_text}</strong>).</p>"
            f"<p><a href='{_app_url('/app/marketplace')}'>Open marketplace</a></p>"
        )
        return TransactionalEmailTemplate(subject=subject, text_body=text, html_body=html)

    if template_key == "password_reset":
        subject = "Reset your Thorpe Workforce password"
        text = (
            f"Hi {name},\n\nUse the link below to reset your password. This link expires soon.\n{reset_url}\n\n"
            "If you did not request this reset, you can ignore this email."
        )
        html = (
            f"<h2>Reset your password</h2><p>Hi {name},</p>"
            f"<p><a href='{reset_url}'>Reset password</a> (expires soon).</p>"
            "<p>If you did not request this reset, you can ignore this email.</p>"
        )
        return TransactionalEmailTemplate(subject=subject, text_body=text, html_body=html)

    if template_key == "support_request_received":
        subject = "We received your support request"
        text = (
            f"Hi {name},\n\nWe received your request and our team will follow up soon.\n"
            f"You can continue using Thorpe Workforce here: {dashboard_url}\n\nSupport: {support_email}"
        )
        html = (
            f"<h2>We received your support request</h2><p>Hi {name},</p>"
            "<p>Our team will follow up soon.</p>"
            f"<p><a href='{dashboard_url}'>Open dashboard</a></p><p>Support: {support_email}</p>"
        )
        return TransactionalEmailTemplate(subject=subject, text_body=text, html_body=html)

    raise ValueError(f"Unsupported transactional template: {template_key}")


def send_transactional_email(
    *,
    to_email: str,
    template_key: str,
    recipient_name: str | None = None,
    context: dict | None = None,
) -> None:
    template = render_template(template_key, recipient_name=recipient_name, context=context)
    provider = get_email_provider()
    provider.send_email(
        SendEmailInput(
            to_email=to_email,
            subject=template.subject,
            body=template.text_body,
            html_body=template.html_body,
        )
    )


def generate_password_reset_token(*, ttl_minutes: int = 60) -> tuple[str, str, datetime]:
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(UTC) + timedelta(minutes=max(ttl_minutes, 5))
    return raw_token, token_hash, expires_at
