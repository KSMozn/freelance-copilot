from __future__ import annotations

import re
from uuid import UUID

from app.domain.entities.skill_catalog import SkillCatalogEntry, SkillCategory
from app.domain.repositories.skill_catalog_repository import SkillCatalogRepository

_SLUG_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    s = name.strip().lower()
    s = _SLUG_NON_ALNUM.sub("-", s).strip("-")
    return s or "unknown"


class SkillCatalogService:
    """Single funnel for normalizing raw skill strings into catalog rows.

    Lookup order (each step short-circuits on a hit):
      1. Exact slug match against `skill_catalog.slug`
      2. Alias slug match against `skill_catalog.aliases`
      3. Fuzzy trigram match against `skill_catalog.name` (similarity ≥ 0.85)
      4. Create a new row marked `is_system_seeded = false`, default
         category `tool` unless an explicit category is supplied

    Used at every ingest seam (CV parser, GitHub scanner, manual entry, etc.)
    so the global pot stays normalized and deduplicated.
    """

    def __init__(
        self,
        catalog_repo: SkillCatalogRepository,
        fuzzy_threshold: float = 0.85,
    ) -> None:
        self._catalog = catalog_repo
        self._threshold = fuzzy_threshold

    async def resolve(
        self,
        raw_name: str,
        *,
        default_category: SkillCategory = "tool",
        created_by_user_id: UUID | None = None,
    ) -> SkillCatalogEntry | None:
        name = (raw_name or "").strip()
        if not name or len(name) > 120:
            return None
        slug = slugify(name)

        hit = await self._catalog.get_by_slug(slug)
        if hit:
            return hit
        hit = await self._catalog.find_by_alias(slug)
        if hit:
            return hit
        hit = await self._catalog.find_by_fuzzy_name(name, self._threshold)
        if hit:
            return hit

        return await self._catalog.create(
            slug=slug,
            name=name,
            category=default_category,
            aliases=[],
            is_system_seeded=False,
            created_by_user_id=created_by_user_id,
        )
