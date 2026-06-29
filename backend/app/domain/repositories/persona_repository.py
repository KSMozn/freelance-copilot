from typing import Any, Protocol
from uuid import UUID

from app.domain.entities.persona import Persona, PersonaArchetype


class PersonaArchetypeRepository(Protocol):
    async def list_active(self) -> list[PersonaArchetype]: ...

    async def get_by_id(self, archetype_id: UUID) -> PersonaArchetype | None: ...

    async def get_by_slug(self, slug: str) -> PersonaArchetype | None: ...


class PersonaRepository(Protocol):
    async def list_for_user(
        self, user_id: UUID, *, include_archived: bool = False
    ) -> list[Persona]: ...

    async def get(self, user_id: UUID, persona_id: UUID) -> Persona | None: ...

    async def get_default(self, user_id: UUID) -> Persona | None: ...

    async def create(self, persona: Persona) -> Persona: ...

    async def update(
        self,
        *,
        user_id: UUID,
        persona_id: UUID,
        patch: dict[str, Any],
    ) -> Persona | None: ...

    async def set_default(self, user_id: UUID, persona_id: UUID) -> None: ...

    async def delete(self, user_id: UUID, persona_id: UUID) -> bool: ...
