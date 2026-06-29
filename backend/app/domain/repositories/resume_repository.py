from typing import Protocol
from uuid import UUID

from app.domain.entities.resume import Resume


class ResumeRepository(Protocol):
    async def create(
        self,
        *,
        user_id: UUID,
        title: str,
        target_role: str | None,
        summary: str | None,
        seniority_level: str | None,
        primary_skills: list[str],
        secondary_skills: list[str],
        industries: list[str],
        domains: list[str],
        achievements: list[str],
        project_highlights: list[str],
        keywords: list[str],
        notes: str | None,
    ) -> Resume: ...

    async def get_by_id(self, resume_id: UUID, *, user_id: UUID) -> Resume | None: ...

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        search: str | None,
        domain: str | None,
        skill: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Resume], int]: ...

    async def list_all_for_user(self, user_id: UUID) -> list[Resume]: ...

    async def update(
        self,
        resume_id: UUID,
        *,
        user_id: UUID,
        fields: dict[str, object],
    ) -> Resume | None: ...

    async def delete(self, resume_id: UUID, *, user_id: UUID) -> bool: ...
