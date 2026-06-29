from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user_skill import UserSkillEntry
from app.infrastructure.db.models.user_skill import UserSkill


def _to_domain(row: UserSkill) -> UserSkillEntry:
    return UserSkillEntry(
        id=row.id,
        user_id=row.user_id,
        skill_id=row.skill_id,
        proficiency=row.proficiency,
        years_experience=row.years_experience,
        sources=dict(row.sources or {}),
        evidence_count=row.evidence_count,
        is_active=row.is_active,
        pinned=row.pinned,
        last_evidence_date=row.last_evidence_date,
        added_at=row.added_at,
        updated_at=row.updated_at,
    )


def _merge_sources(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Union list-valued source ids; OR boolean flags. Pure function."""
    if not existing:
        return dict(incoming)
    merged = dict(existing)
    for key, value in incoming.items():
        prev = merged.get(key)
        if isinstance(value, list):
            seen = set(prev or [])
            for item in value:
                if item not in seen:
                    seen.add(item)
            merged[key] = list(seen)
        elif isinstance(value, bool):
            merged[key] = bool(prev) or value
        else:
            merged[key] = value
    return merged


class SQLAlchemyUserSkillRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(self, user_id: UUID) -> list[UserSkillEntry]:
        stmt = (
            select(UserSkill)
            .where(UserSkill.user_id == user_id)
            .where(UserSkill.is_active.is_(True))
            .order_by(UserSkill.proficiency.desc(), UserSkill.evidence_count.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_domain(r) for r in rows]

    async def get(self, user_id: UUID, skill_id: UUID) -> UserSkillEntry | None:
        stmt = select(UserSkill).where(
            UserSkill.user_id == user_id, UserSkill.skill_id == skill_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

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
        stmt = select(UserSkill).where(
            UserSkill.user_id == user_id, UserSkill.skill_id == skill_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            row = UserSkill(
                user_id=user_id,
                skill_id=skill_id,
                proficiency=proficiency if proficiency is not None else 3,
                sources=dict(sources or {}),
                evidence_count=(
                    evidence_count if evidence_count is not None else 0
                ),
                pinned=bool(pinned) if pinned is not None else False,
            )
            self._session.add(row)
        else:
            if proficiency is not None:
                row.proficiency = proficiency
            if sources is not None:
                row.sources = _merge_sources(dict(row.sources or {}), sources)
            if evidence_count is not None:
                row.evidence_count = max(row.evidence_count, evidence_count)
            if pinned is not None:
                row.pinned = pinned
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _to_domain(row)

    async def deactivate(self, user_id: UUID, skill_id: UUID) -> None:
        stmt = select(UserSkill).where(
            UserSkill.user_id == user_id, UserSkill.skill_id == skill_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return
        row.is_active = False
        await self._session.commit()
