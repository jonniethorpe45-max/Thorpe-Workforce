import uuid

from app.integrations.email.base import EmailProvider, SendEmailInput, SendEmailResult


class MockEmailProvider(EmailProvider):
    def send_email(self, payload: SendEmailInput) -> SendEmailResult:
        return SendEmailResult(provider_message_id=f"mock-{uuid.uuid4()}", status="sent")
