from app.core.config import settings
from app.integrations.ai.base import AIProvider
from app.integrations.ai.mock_provider import MockAIProvider


def get_ai_provider() -> AIProvider:
    # MVP defaults to mock provider for local development.
    if settings.ai_provider == "mock":
        return MockAIProvider()
    return MockAIProvider()
