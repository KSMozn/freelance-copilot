from typing import Protocol
from uuid import UUID

from app.domain.entities.skill_catalog import SkillCatalogEntry, SkillCategory


class SkillCatalogRepository(Protocol):
    async def get_by_id(self, skill_id: UUID) -> SkillCatalogEntry | None: ...

    async def get_by_slug(self, slug: str) -> SkillCatalogEntry | None: ...

    async def find_by_alias(self, alias_slug: str) -> SkillCatalogEntry | None: ...

    async def find_by_fuzzy_name(
        self, name: str, threshold: float = 0.85
    ) -> SkillCatalogEntry | None: ...

    async def create(
        self,
        *,
        slug: str,
        name: str,
        category: SkillCategory,
        aliases: list[str] | None = None,
        is_system_seeded: bool = False,
        created_by_user_id: UUID | None = None,
    ) -> SkillCatalogEntry: ...

    async def list_all(self) -> list[SkillCatalogEntry]: ...
