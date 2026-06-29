from app.core.config import Settings
from app.domain.providers.email_provider import EmailProvider
from app.infrastructure.email.errors import EmailProviderUnavailable
from app.infrastructure.email.mock_provider import MockEmailProvider
from app.infrastructure.email.resend_provider import ResendEmailProvider


def build_email_provider(settings: Settings) -> EmailProvider:
    """Return the configured email provider, falling back to mock when keys are missing."""
    provider = settings.email_provider
    if provider == "mock":
        return MockEmailProvider()
    if provider == "resend":
        if not settings.resend_api_key:
            raise EmailProviderUnavailable(
                "EMAIL_PROVIDER=resend but RESEND_API_KEY is not set. "
                "Either set the key or use EMAIL_PROVIDER=mock for local development."
            )
        return ResendEmailProvider(
            api_key=settings.resend_api_key,
            from_address=settings.email_from_address,
            from_name=settings.email_from_name,
        )
    raise EmailProviderUnavailable(f"Unknown EMAIL_PROVIDER: {provider!r}")
