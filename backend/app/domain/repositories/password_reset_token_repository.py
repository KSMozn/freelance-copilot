from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.entities.password_reset_token import PasswordResetToken


class PasswordResetTokenRepository(Protocol):
    """Issuance-side contract. Implementations must not hold a transaction,
    connection, or lock across calls — the service interleaves these with an
    external email-provider round-trip."""

    async def create(
        self,
        *,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken: ...

    async def delete(self, token_id: UUID) -> None: ...

    async def get_by_token_hash(
        self, token_hash: str
    ) -> PasswordResetToken | None: ...

    async def invalidate_older_active_for_user(
        self, user_id: UUID, newest_token_id: UUID, at: datetime
    ) -> None: ...


class PasswordResetCommitter(Protocol):
    async def consume(
        self,
        *,
        token_id: UUID,
        user_id: UUID,
        password_hash: str,
        at: datetime,
    ) -> bool: ...
