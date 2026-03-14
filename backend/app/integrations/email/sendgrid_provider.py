import uuid

import requests

from app.core.config import settings
from app.integrations.email.base import EmailProvider, SendEmailInput, SendEmailResult


class SendGridProvider(EmailProvider):
    def send_email(self, payload: SendEmailInput) -> SendEmailResult:
        if not settings.sendgrid_api_key:
            # Safe fallback for local environments
            return SendEmailResult(provider_message_id=f"sendgrid-local-{uuid.uuid4()}", status="queued")

        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {settings.sendgrid_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": payload.to_email}]}],
                "from": {"email": settings.sendgrid_from_email},
                "subject": payload.subject,
                "content": [{"type": "text/plain", "value": payload.body}],
            },
            timeout=10,
        )
        response.raise_for_status()
        provider_message_id = response.headers.get("X-Message-Id", f"sendgrid-{uuid.uuid4()}")
        return SendEmailResult(provider_message_id=provider_message_id, status="sent")
