from app.core.config import Settings
from app.domain.providers.embedding_provider import EmbeddingProvider
from app.infrastructure.ai.errors import AIProviderUnavailable
from app.infrastructure.ai.mock_embedding_provider import MockEmbeddingProvider
from app.infrastructure.ai.openai_embedding_provider import OpenAIEmbeddingProvider


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    """Return the configured embedding provider.

    Falls back hard rather than silently switching to mock when the configured
    provider is missing credentials — surprise downgrades make scoring drift
    impossible to debug.
    """
    provider = settings.embedding_provider
    if provider == "mock":
        return MockEmbeddingProvider()
    if provider == "openai":
        if not settings.openai_api_key:
            raise AIProviderUnavailable(
                "EMBEDDING_PROVIDER=openai but OPENAI_API_KEY is not set. "
                "Either set the key or use EMBEDDING_PROVIDER=mock for offline use."
            )
        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
        )
    raise AIProviderUnavailable(f"Unknown EMBEDDING_PROVIDER: {provider!r}")
