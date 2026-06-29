from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.persona import Persona as DomainPersona
from app.domain.entities.persona import PersonaArchetype as DomainArchetype
from app.infrastructure.db.models.persona import Persona, PersonaArchetype


def _archetype_to_domain(row: PersonaArchetype) -> DomainArchetype:
    return DomainArchetype(
        id=row.id,
        slug=row.slug,
        name=row.name,
        description=row.description,
        default_weights=dict(row.default_weights or {}),
        default_skill_category_weights=dict(row.default_skill_category_weights or {}),
        default_proposal_tone=row.default_proposal_tone,  # type: ignore[arg-type]
        default_target_roles=list(row.default_target_roles or []),
        default_seniority_band=row.default_seniority_band,
        is_active=row.is_active,
        sort_order=row.sort_order,
        created_at=row.created_at,
    )


def _persona_to_domain(row: Persona) -> DomainPersona:
    return DomainPersona(
        id=row.id,
        user_id=row.user_id,
        archetype_id=row.archetype_id,
        name=row.name,
        target_role=row.target_role,
        target_seniority=row.target_seniority,
        weights=dict(row.weights or {}),
        skill_category_weights=dict(row.skill_category_weights or {}),
        proposal_tone=row.proposal_tone,  # type: ignore[arg-type]
        strategic_priorities=list(row.strategic_priorities or []),
        pinned_experience_ids=list(row.pinned_experience_ids or []),
        pinned_project_ids=list(row.pinned_project_ids or []),
        pinned_skill_ids=list(row.pinned_skill_ids or []),
        accent_color=row.accent_color,
        is_default=row.is_default,
        is_archived=row.is_archived,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SQLAlchemyPersonaArchetypeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[DomainArchetype]:
        stmt = (
            select(PersonaArchetype)
            .where(PersonaArchetype.is_active.is_(True))
            .order_by(PersonaArchetype.sort_order, PersonaArchetype.name)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_archetype_to_domain(r) for r in rows]

    async def get_by_id(self, archetype_id: UUID) -> DomainArchetype | None:
        row = await self._session.get(PersonaArchetype, archetype_id)
        return _archetype_to_domain(row) if row else None

    async def get_by_slug(self, slug: str) -> DomainArchetype | None:
        stmt = select(PersonaArchetype).where(PersonaArchetype.slug == slug)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _archetype_to_domain(row) if row else None


class SQLAlchemyPersonaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(
        self, user_id: UUID, *, include_archived: bool = False
    ) -> list[DomainPersona]:
        stmt = select(Persona).where(Persona.user_id == user_id)
        if not include_archived:
            stmt = stmt.where(Persona.is_archived.is_(False))
        stmt = stmt.order_by(Persona.is_default.desc(), Persona.created_at)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_persona_to_domain(r) for r in rows]

    async def get(self, user_id: UUID, persona_id: UUID) -> DomainPersona | None:
        stmt = select(Persona).where(
            Persona.id == persona_id, Persona.user_id == user_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _persona_to_domain(row) if row else None

    async def get_default(self, user_id: UUID) -> DomainPersona | None:
        stmt = (
            select(Persona)
            .where(Persona.user_id == user_id)
            .where(Persona.is_default.is_(True))
            .where(Persona.is_archived.is_(False))
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _persona_to_domain(row) if row else None

    async def create(self, persona: DomainPersona) -> DomainPersona:
        row = Persona(
            id=persona.id,
            user_id=persona.user_id,
            archetype_id=persona.archetype_id,
            name=persona.name,
            target_role=persona.target_role,
            target_seniority=persona.target_seniority,
            weights=dict(persona.weights or {}),
            skill_category_weights=dict(persona.skill_category_weights or {}),
            proposal_tone=persona.proposal_tone,
            strategic_priorities=list(persona.strategic_priorities or []),
            pinned_experience_ids=list(persona.pinned_experience_ids or []),
            pinned_project_ids=list(persona.pinned_project_ids or []),
            pinned_skill_ids=list(persona.pinned_skill_ids or []),
            accent_color=persona.accent_color,
            is_default=persona.is_default,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _persona_to_domain(row)

    async def update(
        self,
        *,
        user_id: UUID,
        persona_id: UUID,
        patch: dict[str, Any],
    ) -> DomainPersona | None:
        stmt = select(Persona).where(
            Persona.id == persona_id, Persona.user_id == user_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        for key, value in patch.items():
            if hasattr(row, key):
                setattr(row, key, value)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _persona_to_domain(row)

    async def set_default(self, user_id: UUID, persona_id: UUID) -> None:
        # Clear current default, then mark target. Two statements in one txn
        # — the partial unique index prevents two defaults coexisting.
        await self._session.execute(
            update(Persona)
            .where(Persona.user_id == user_id, Persona.is_default.is_(True))
            .values(is_default=False)
        )
        await self._session.execute(
            update(Persona)
            .where(Persona.user_id == user_id, Persona.id == persona_id)
            .values(is_default=True)
        )
        await self._session.commit()

    async def delete(self, user_id: UUID, persona_id: UUID) -> bool:
        row = await self.get(user_id, persona_id)
        if row is None:
            return False
        sa_row = await self._session.get(Persona, persona_id)
        if sa_row is None:
            return False
        await self._session.delete(sa_row)
        await self._session.commit()
        return True
