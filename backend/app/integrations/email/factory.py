from app.core.config import settings
from app.integrations.email.base import EmailProvider
from app.integrations.email.mock_provider import MockEmailProvider
from app.integrations.email.sendgrid_provider import SendGridProvider


def get_email_provider() -> EmailProvider:
    if settings.email_provider == "sendgrid":
        return SendGridProvider()
    return MockEmailProvider()
