from datetime import date
from typing import Protocol
from uuid import UUID

from app.domain.entities.experience import Experience


class ExperienceRepository(Protocol):
    async def list_for_user(self, user_id: UUID) -> list[Experience]: ...

    async def find_match(
        self,
        *,
        user_id: UUID,
        company: str,
        role: str,
        start_date: date | None,
    ) -> Experience | None:
        """Best-effort dedup lookup used by ingestion paths.

        Match is (user_id, lower(company), lower(role)) with start_date as a
        tiebreaker — keeps re-importing the same CV from idempotently
        duplicating experience rows.
        """
        ...

    async def create(
        self,
        *,
        user_id: UUID,
        company: str,
        role: str,
        location: str | None,
        employment_type: str | None,
        start_date: date | None,
        end_date: date | None,
        summary: str | None,
        source: str,
        source_ref: UUID | None,
        skill_ids: list[UUID],
        achievements: list[str],
    ) -> Experience: ...

    async def add_skills(
        self, *, experience_id: UUID, skill_ids: list[UUID]
    ) -> None: ...
