from app.core.config import settings
from app.integrations.ai.base import AIProvider
from app.integrations.ai.mock_provider import MockAIProvider


def get_ai_provider() -> AIProvider:
    # MVP keeps a safe local default while preserving provider abstraction boundaries.
    if settings.ai_provider in {"mock", "openai", "anthropic"}:
        return MockAIProvider()
    return MockAIProvider()
