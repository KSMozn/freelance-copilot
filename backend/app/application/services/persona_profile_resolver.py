from __future__ import annotations

from uuid import UUID

from app.domain.entities.persona import Persona, PersonaArchetype
from app.domain.entities.skill_catalog import SkillCatalogEntry
from app.domain.entities.user_skill import UserSkillEntry
from app.domain.profiles.freelancer_profile import (
    DEFAULT_FREELANCER_PROFILE,
    FreelancerProfile,
)
from app.domain.repositories.persona_repository import (
    PersonaArchetypeRepository,
    PersonaRepository,
)
from app.domain.repositories.skill_catalog_repository import SkillCatalogRepository
from app.domain.repositories.user_skill_repository import UserSkillRepository


# Categories that contribute to "strong skills" (technical-fit signal).
_SKILL_CATEGORIES = {
    "language",
    "framework",
    "tool",
    "platform",
    "database",
    "practice",
    "leadership",
}

# Categories considered domain knowledge — promoted to `strong_domains`.
_DOMAIN_CATEGORIES = {"domain"}

# Proficiency threshold for a skill to count as "strong."
_STRONG_PROFICIENCY = 4


class PersonaProfileResolver:
    """Produces the legacy ``FreelancerProfile`` shape from the knowledge graph.

    Three load paths:
      * ``load_for_persona(persona_id)`` — preferred. Returns weights /
        priorities / target role derived from persona + its archetype.
      * ``load_for_user(user_id)`` — uses the user's default persona if one
        exists, otherwise falls back to user_skills + DEFAULT_FREELANCER_PROFILE.
      * Empty pot, no personas → ``DEFAULT_FREELANCER_PROFILE`` verbatim so
        freshly signed-up users still get a baseline scoring behaviour.

    Scoring engine code is untouched — only this producer changes.
    """

    def __init__(
        self,
        *,
        user_skills: UserSkillRepository,
        skill_catalog: SkillCatalogRepository,
        personas: PersonaRepository,
        archetypes: PersonaArchetypeRepository,
        fallback: FreelancerProfile = DEFAULT_FREELANCER_PROFILE,
    ) -> None:
        self._user_skills = user_skills
        self._catalog = skill_catalog
        self._personas = personas
        self._archetypes = archetypes
        self._fallback = fallback

    # ---- Public ----------------------------------------------------------

    async def load_for_user(self, user_id: UUID) -> FreelancerProfile:
        persona = await self._personas.get_default(user_id)
        if persona is not None:
            return await self._load_with_persona(user_id, persona)
        return await self._load_user_only(user_id)

    async def load_for_persona(
        self, *, user_id: UUID, persona_id: UUID
    ) -> FreelancerProfile:
        persona = await self._personas.get(user_id, persona_id)
        if persona is None:
            # Caller passed a stale persona id — fall back gracefully.
            return await self.load_for_user(user_id)
        return await self._load_with_persona(user_id, persona)

    # ---- Internals -------------------------------------------------------

    async def _load_user_only(self, user_id: UUID) -> FreelancerProfile:
        rows = await self._user_skills.list_for_user(user_id)
        if not rows:
            return self._fallback

        catalog_by_id = await self._catalog_for_rows(rows)
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

    async def _load_with_persona(
        self, user_id: UUID, persona: Persona
    ) -> FreelancerProfile:
        archetype = await self._archetypes.get_by_id(persona.archetype_id)
        rows = await self._user_skills.list_for_user(user_id)
        catalog_by_id = await self._catalog_for_rows(rows)
        strong_skills, strong_domains = _split_by_category(rows, catalog_by_id)

        weights = _merge_weights(persona, archetype, self._fallback.weights)
        priorities = _resolve_priorities(persona, self._fallback.strategic_priorities)

        # Pinned skills always surface in strong_skills, even if below the
        # proficiency threshold — the user has explicitly promoted them.
        if persona.pinned_skill_ids:
            pinned_set = {str(s) for s in persona.pinned_skill_ids}
            pinned_names = [
                catalog_by_id[row.skill_id].name
                for row in rows
                if str(row.skill_id) in pinned_set and row.skill_id in catalog_by_id
            ]
            existing_lower = {s.lower() for s in strong_skills}
            for name in pinned_names:
                if name.lower() not in existing_lower:
                    strong_skills.insert(0, name)
                    existing_lower.add(name.lower())

        return FreelancerProfile(
            version=f"persona:{persona.id}",
            strong_skills=tuple(strong_skills) or self._fallback.strong_skills,
            strong_domains=tuple(strong_domains) or self._fallback.strong_domains,
            strategic_priorities=tuple(priorities),
            weights=weights,
        )

    async def _catalog_for_rows(
        self, rows: list[UserSkillEntry]
    ) -> dict[UUID, SkillCatalogEntry]:
        catalog: dict[UUID, SkillCatalogEntry] = {}
        for row in rows:
            entry = await self._catalog.get_by_id(row.skill_id)
            if entry is not None:
                catalog[row.skill_id] = entry
        return catalog


# ---- Pure helpers (testable without DB) ---------------------------------


def _split_by_category(
    rows: list[UserSkillEntry],
    catalog_by_id: dict[UUID, SkillCatalogEntry],
) -> tuple[list[str], list[str]]:
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


def _merge_weights(
    persona: Persona,
    archetype: PersonaArchetype | None,
    fallback: dict[str, int],
) -> dict[str, int]:
    """Effective scoring weights: fallback ← archetype ← persona overrides.

    Persona-level keys win over archetype defaults, which win over the
    legacy hard-coded fallback (so any new dimension added later still
    contributes by default).
    """
    merged: dict[str, int] = dict(fallback)
    if archetype and archetype.default_weights:
        merged.update({k: int(v) for k, v in archetype.default_weights.items()})
    if persona.weights:
        merged.update({k: int(v) for k, v in persona.weights.items()})
    return merged


def _resolve_priorities(persona: Persona, fallback: tuple[str, ...]) -> list[str]:
    if persona.strategic_priorities:
        return [str(p) for p in persona.strategic_priorities]
    return list(fallback)
