class DomainError(Exception):
    """Base class for errors raised from the domain layer."""


class NotFoundError(DomainError):
    pass


class AlreadyExistsError(DomainError):
    pass


class InvalidCredentialsError(DomainError):
    pass


class PermissionDeniedError(DomainError):
    pass


class RateLimitedError(DomainError):
    """Too many requests in a short window (e.g. OTP issuance)."""


class OtpInvalidError(DomainError):
    """Submitted OTP code is wrong, expired, exhausted attempts, or missing."""


class PasswordResetInvalidError(DomainError):
    """Password-reset token is unknown, already used, or expired."""


class EmailDeliveryError(DomainError):
    """The configured email provider failed to deliver a message."""
