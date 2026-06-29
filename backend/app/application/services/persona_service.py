from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from app.domain.entities.persona import Persona, PersonaArchetype
from app.domain.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    PermissionDeniedError,
)
from app.domain.repositories.persona_repository import (
    PersonaArchetypeRepository,
    PersonaRepository,
)

PRIMARY_ARCHETYPE_SLUG = "senior_engineer"
PRIMARY_PERSONA_NAME = "Primary"


class PersonaService:
    """CRUD + lifecycle for user personas.

    Two responsibilities worth flagging:
      * `ensure_primary` is called from `AuthService.verify_otp` when a brand
        new account is created, so every user lands on the dashboard with
        a working default persona (no empty-state).
      * `delete` refuses to delete the last persona — every user must have
        at least one. Use `archive` (sets `is_archived=true`) to soft-hide.
    """

    def __init__(
        self,
        *,
        personas: PersonaRepository,
        archetypes: PersonaArchetypeRepository,
    ) -> None:
        self._personas = personas
        self._archetypes = archetypes

    # ---- Archetype reads -----------------------------------------------

    async def list_archetypes(self) -> list[PersonaArchetype]:
        return await self._archetypes.list_active()

    async def get_archetype(self, slug_or_id: str | UUID) -> PersonaArchetype | None:
        if isinstance(slug_or_id, UUID):
            return await self._archetypes.get_by_id(slug_or_id)
        return await self._archetypes.get_by_slug(slug_or_id)

    # ---- Persona CRUD --------------------------------------------------

    async def list_for_user(self, user_id: UUID) -> list[Persona]:
        return await self._personas.list_for_user(user_id)

    async def get(self, user_id: UUID, persona_id: UUID) -> Persona:
        persona = await self._personas.get(user_id, persona_id)
        if persona is None:
            raise NotFoundError("Persona not found")
        return persona

    async def resolve_default(self, user_id: UUID) -> Persona | None:
        return await self._personas.get_default(user_id)

    async def instantiate_from_archetype(
        self,
        *,
        user_id: UUID,
        archetype_slug: str,
        name: str | None = None,
        target_role: str | None = None,
        is_default: bool = False,
    ) -> Persona:
        archetype = await self._archetypes.get_by_slug(archetype_slug)
        if archetype is None:
            raise NotFoundError(f"Archetype '{archetype_slug}' not found")

        # Default name strategy: use the archetype name unless it would
        # collide with an existing persona for this user. Then suffix.
        chosen_name = (name or archetype.name).strip()[:120]
        existing = await self._personas.list_for_user(user_id, include_archived=True)
        if any(p.name.lower() == chosen_name.lower() for p in existing):
            for n in range(2, 50):
                candidate = f"{chosen_name} {n}"
                if not any(p.name.lower() == candidate.lower() for p in existing):
                    chosen_name = candidate
                    break
            else:
                raise AlreadyExistsError("Could not generate a unique persona name")

        # First persona is always default, regardless of the flag.
        if not existing:
            is_default = True

        persona = Persona(
            id=uuid4(),
            user_id=user_id,
            archetype_id=archetype.id,
            name=chosen_name,
            target_role=(target_role or "").strip()[:255] or None,
            target_seniority=archetype.default_seniority_band,
            is_default=is_default,
        )
        created = await self._personas.create(persona)

        if is_default:
            # Make sure no other persona still claims default.
            await self._personas.set_default(user_id, created.id)
        return created

    async def ensure_primary(self, user_id: UUID) -> Persona:
        """Idempotent: returns the user's default persona, creating one if absent."""
        existing = await self._personas.get_default(user_id)
        if existing is not None:
            return existing
        # No default — but maybe they have a non-default already? If so,
        # promote the first one rather than creating duplicates.
        all_personas = await self._personas.list_for_user(user_id)
        if all_personas:
            await self._personas.set_default(user_id, all_personas[0].id)
            return (await self._personas.get_default(user_id)) or all_personas[0]
        return await self.instantiate_from_archetype(
            user_id=user_id,
            archetype_slug=PRIMARY_ARCHETYPE_SLUG,
            name=PRIMARY_PERSONA_NAME,
            is_default=True,
        )

    async def update(
        self,
        *,
        user_id: UUID,
        persona_id: UUID,
        patch: dict[str, Any],
    ) -> Persona:
        # Whitelist updatable fields so callers can't poke at user_id, etc.
        allowed = {
            "name",
            "target_role",
            "target_seniority",
            "weights",
            "skill_category_weights",
            "proposal_tone",
            "strategic_priorities",
            "pinned_experience_ids",
            "pinned_project_ids",
            "pinned_skill_ids",
            "accent_color",
            "is_archived",
        }
        clean = {k: v for k, v in patch.items() if k in allowed}
        updated = await self._personas.update(
            user_id=user_id, persona_id=persona_id, patch=clean
        )
        if updated is None:
            raise NotFoundError("Persona not found")
        return updated

    async def set_default(self, user_id: UUID, persona_id: UUID) -> Persona:
        # Verify ownership before flipping defaults.
        target = await self._personas.get(user_id, persona_id)
        if target is None:
            raise NotFoundError("Persona not found")
        await self._personas.set_default(user_id, persona_id)
        return (await self._personas.get(user_id, persona_id)) or target

    async def delete(self, user_id: UUID, persona_id: UUID) -> None:
        all_personas = await self._personas.list_for_user(user_id)
        if not any(p.id == persona_id for p in all_personas):
            raise NotFoundError("Persona not found")
        if len(all_personas) <= 1:
            raise PermissionDeniedError(
                "Cannot delete the only persona. Create another first."
            )
        target = next(p for p in all_personas if p.id == persona_id)
        ok = await self._personas.delete(user_id, persona_id)
        if not ok:
            raise NotFoundError("Persona not found")
        if target.is_default:
            # Promote the next persona to default so the user always has one.
            remaining = await self._personas.list_for_user(user_id)
            if remaining:
                await self._personas.set_default(user_id, remaining[0].id)
