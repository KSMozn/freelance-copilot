from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.entities.password_reset_token import PasswordResetToken


class PasswordResetTokenRepository(Protocol):
    async def create(
        self,
        *,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken: ...

    async def get_by_token_hash(
        self, token_hash: str
    ) -> PasswordResetToken | None: ...

    async def mark_used(self, token_id: UUID, used_at: datetime) -> None: ...

    async def invalidate_active_for_user(
        self, user_id: UUID, at: datetime
    ) -> None: ...
