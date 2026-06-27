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
