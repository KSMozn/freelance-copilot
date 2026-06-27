class AIProviderError(Exception):
    """Wraps any failure originating from an LLM provider."""


class AIProviderUnavailable(AIProviderError):
    """The provider could not be reached, is missing credentials, or timed out."""


class AIProviderResponseError(AIProviderError):
    """The provider responded with a non-2xx status."""


class AIProviderParseError(AIProviderError):
    """The provider returned a 200 but the body was not JSON or did not match the schema."""
