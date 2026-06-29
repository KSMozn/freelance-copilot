from typing import Any, Protocol
from uuid import UUID

from app.domain.entities.user_skill import UserSkillEntry


class UserSkillRepository(Protocol):
    async def list_for_user(self, user_id: UUID) -> list[UserSkillEntry]: ...

    async def get(self, user_id: UUID, skill_id: UUID) -> UserSkillEntry | None: ...

    async def upsert(
        self,
        *,
        user_id: UUID,
        skill_id: UUID,
        proficiency: int | None = None,
        sources: dict[str, Any] | None = None,
        evidence_count: int | None = None,
        pinned: bool | None = None,
    ) -> UserSkillEntry:
        """Insert or update a (user, skill) row.

        Implementations should merge `sources` into any existing JSONB rather
        than overwriting — every new evidence row is additive.
        """
        ...

    async def deactivate(self, user_id: UUID, skill_id: UUID) -> None: ...
