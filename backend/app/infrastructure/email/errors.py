class EmailProviderError(RuntimeError):
    """Raised when the configured email provider cannot deliver a message."""


class EmailProviderUnavailable(EmailProviderError):
    """Raised when required configuration (API key, sender domain) is missing."""
