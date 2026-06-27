from app.core.config import Settings
from app.domain.providers.ai_provider import AIProvider
from app.infrastructure.ai.claude_provider import ClaudeProvider
from app.infrastructure.ai.errors import AIProviderUnavailable
from app.infrastructure.ai.mock_provider import MockAIProvider
from app.infrastructure.ai.openai_provider import OpenAIProvider


def build_ai_provider(settings: Settings) -> AIProvider:
    """Return the configured AI provider, falling back to mock when keys are missing."""
    provider = settings.ai_provider
    if provider == "mock":
        return MockAIProvider()
    if provider == "openai":
        if not settings.openai_api_key:
            raise AIProviderUnavailable(
                "AI_PROVIDER=openai but OPENAI_API_KEY is not set. "
                "Either set the key or use AI_PROVIDER=mock for local development."
            )
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )
    if provider == "claude":
        if not settings.anthropic_api_key:
            raise AIProviderUnavailable(
                "AI_PROVIDER=claude but ANTHROPIC_API_KEY is not set. "
                "Either set the key or use AI_PROVIDER=mock for local development."
            )
        return ClaudeProvider(
            api_key=settings.anthropic_api_key,
            model=settings.claude_model,
        )
    raise AIProviderUnavailable(f"Unknown AI_PROVIDER: {provider!r}")
