from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.entities.user import User


class UserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> User | None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def create(
        self,
        *,
        email: str,
        password_hash: str | None,
        full_name: str | None,
        email_verified_at: datetime | None = None,
        selected_persona_kind: str = "professional",
    ) -> User: ...

    async def mark_email_verified(
        self, user_id: UUID, verified_at: datetime
    ) -> None: ...

    async def set_password(self, user_id: UUID, password_hash: str) -> None: ...

    async def touch_last_login(self, user_id: UUID, at: datetime) -> None: ...

    async def set_persona_kind(self, user_id: UUID, kind: str) -> None: ...
