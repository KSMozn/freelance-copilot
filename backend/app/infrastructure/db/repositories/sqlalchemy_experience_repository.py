from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.experience import Experience as DomainExperience
from app.infrastructure.db.models.experience import (
    Experience,
    ExperienceAchievement,
    ExperienceSkill,
)


def _to_domain(row: Experience, skill_ids: list[UUID]) -> DomainExperience:
    return DomainExperience(
        id=row.id,
        user_id=row.user_id,
        company=row.company,
        role=row.role,
        location=row.location,
        employment_type=row.employment_type,  # type: ignore[arg-type]
        start_date=row.start_date,
        end_date=row.end_date,
        summary=row.summary,
        source=row.source,  # type: ignore[arg-type]
        source_ref=row.source_ref,
        skill_ids=skill_ids,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SQLAlchemyExperienceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(self, user_id: UUID) -> list[DomainExperience]:
        stmt = (
            select(Experience)
            .where(Experience.user_id == user_id)
            .order_by(Experience.start_date.desc().nullslast())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        result: list[DomainExperience] = []
        for row in rows:
            skill_ids = await self._skill_ids_for(row.id)
            result.append(_to_domain(row, skill_ids))
        return result

    async def find_match(
        self,
        *,
        user_id: UUID,
        company: str,
        role: str,
        start_date: date | None,
    ) -> DomainExperience | None:
        # Case-insensitive match on (company, role). Re-imports of the same
        # CV should not re-create the row.
        stmt = (
            select(Experience)
            .where(Experience.user_id == user_id)
            .where(func.lower(Experience.company) == company.lower())
            .where(func.lower(Experience.role) == role.lower())
        )
        if start_date is not None:
            stmt = stmt.where(Experience.start_date == start_date)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        skill_ids = await self._skill_ids_for(row.id)
        return _to_domain(row, skill_ids)

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
    ) -> DomainExperience:
        row = Experience(
            user_id=user_id,
            company=company,
            role=role,
            location=location,
            employment_type=employment_type,
            start_date=start_date,
            end_date=end_date,
            summary=summary,
            source=source,
            source_ref=source_ref,
        )
        self._session.add(row)
        await self._session.flush()
        for sid in skill_ids:
            self._session.add(ExperienceSkill(experience_id=row.id, skill_id=sid))
        for statement in achievements:
            if statement and statement.strip():
                self._session.add(
                    ExperienceAchievement(
                        experience_id=row.id, statement=statement.strip()
                    )
                )
        await self._session.commit()
        await self._session.refresh(row)
        return _to_domain(row, list(skill_ids))

    async def add_skills(
        self, *, experience_id: UUID, skill_ids: list[UUID]
    ) -> None:
        existing = set(await self._skill_ids_for(experience_id))
        new = [s for s in skill_ids if s not in existing]
        if not new:
            return
        for sid in new:
            self._session.add(
                ExperienceSkill(experience_id=experience_id, skill_id=sid)
            )
        await self._session.commit()

    async def _skill_ids_for(self, experience_id: UUID) -> list[UUID]:
        stmt = select(ExperienceSkill.skill_id).where(
            ExperienceSkill.experience_id == experience_id
        )
        return list((await self._session.execute(stmt)).scalars().all())
