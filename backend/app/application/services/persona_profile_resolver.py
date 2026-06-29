from __future__ import annotations

from uuid import UUID

from app.domain.entities.skill_catalog import SkillCatalogEntry
from app.domain.entities.user_skill import UserSkillEntry
from app.domain.profiles.freelancer_profile import (
    DEFAULT_FREELANCER_PROFILE,
    FreelancerProfile,
)
from app.domain.repositories.skill_catalog_repository import SkillCatalogRepository
from app.domain.repositories.user_skill_repository import UserSkillRepository


# Categories considered "domain knowledge" rather than tech. Phase B promotes
# these into the `strong_domains` tuple; Phase C will let personas override.
_DOMAIN_CATEGORIES = {"domain"}

# Categories that contribute to "strong skills" (the technical-fit signal).
_SKILL_CATEGORIES = {"language", "framework", "tool", "platform", "database", "practice"}

# Proficiency threshold below which a user's skill is not "strong" enough to
# count toward technical_fit at full weight. Future personas may override.
_STRONG_PROFICIENCY = 4


class PersonaProfileResolver:
    """Produce the legacy ``FreelancerProfile`` shape from per-user graph data.

    Phase B replaces the static ``DEFAULT_FREELANCER_PROFILE`` reads with a
    resolver that hydrates per user — so scoring code stays untouched but
    every user now sees their *own* skills/domains drive the score. Phase C
    will plug personas in as additional filters on top of this output.

    For users with an empty pot (no portfolios/resumes/repos yet), this falls
    back to ``DEFAULT_FREELANCER_PROFILE`` so freshly signed-up accounts still
    get a baseline scoring behaviour.
    """

    def __init__(
        self,
        *,
        user_skills: UserSkillRepository,
        skill_catalog: SkillCatalogRepository,
        fallback: FreelancerProfile = DEFAULT_FREELANCER_PROFILE,
    ) -> None:
        self._user_skills = user_skills
        self._catalog = skill_catalog
        self._fallback = fallback

    async def load_for_user(self, user_id: UUID) -> FreelancerProfile:
        rows = await self._user_skills.list_for_user(user_id)
        if not rows:
            return self._fallback

        # Batch-fetch the catalog rows we need so we can group by category.
        catalog_by_id: dict[UUID, SkillCatalogEntry] = {}
        for row in rows:
            entry = await self._catalog.get_by_id(row.skill_id)
            if entry is not None:
                catalog_by_id[row.skill_id] = entry

        strong_skills, strong_domains = _split_by_category(rows, catalog_by_id)
        if not strong_skills and not strong_domains:
            return self._fallback

        return FreelancerProfile(
            version=f"user:{user_id}",
            strong_skills=tuple(strong_skills) or self._fallback.strong_skills,
            strong_domains=tuple(strong_domains) or self._fallback.strong_domains,
            strategic_priorities=self._fallback.strategic_priorities,
            weights=dict(self._fallback.weights),
        )


def _split_by_category(
    rows: list[UserSkillEntry],
    catalog_by_id: dict[UUID, SkillCatalogEntry],
) -> tuple[list[str], list[str]]:
    """Pure helper: bucket user skills into strong technical skills + domains."""
    skills: list[str] = []
    domains: list[str] = []
    for row in rows:
        entry = catalog_by_id.get(row.skill_id)
        if entry is None:
            continue
        if entry.category in _DOMAIN_CATEGORIES:
            domains.append(entry.name)
        elif entry.category in _SKILL_CATEGORIES and row.proficiency >= _STRONG_PROFICIENCY:
            skills.append(entry.name)
    return skills, domains
