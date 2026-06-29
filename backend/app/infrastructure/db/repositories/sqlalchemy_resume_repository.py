from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.resume import Resume as DomainResume
from app.infrastructure.db.models.resume import Resume as ResumeModel


def _to_domain(row: ResumeModel) -> DomainResume:
    return DomainResume(
        id=row.id,
        user_id=row.user_id,
        title=row.title,
        target_role=row.target_role,
        summary=row.summary,
        seniority_level=row.seniority_level,
        primary_skills=list(row.primary_skills or []),
        secondary_skills=list(row.secondary_skills or []),
        industries=list(row.industries or []),
        domains=list(row.domains or []),
        achievements=list(row.achievements or []),
        project_highlights=list(row.project_highlights or []),
        keywords=list(row.keywords or []),
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SQLAlchemyResumeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
    ) -> DomainResume:
        row = ResumeModel(
            user_id=user_id,
            title=title,
            target_role=target_role,
            summary=summary,
            seniority_level=seniority_level,
            primary_skills=primary_skills,
            secondary_skills=secondary_skills,
            industries=industries,
            domains=domains,
            achievements=achievements,
            project_highlights=project_highlights,
            keywords=keywords,
            notes=notes,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _to_domain(row)

    async def get_by_id(self, resume_id: UUID, *, user_id: UUID) -> DomainResume | None:
        stmt = select(ResumeModel).where(
            ResumeModel.id == resume_id, ResumeModel.user_id == user_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        search: str | None,
        domain: str | None,
        skill: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[DomainResume], int]:
        stmt = select(ResumeModel).where(ResumeModel.user_id == user_id)
        count_stmt = select(func.count(ResumeModel.id)).where(
            ResumeModel.user_id == user_id
        )
        if search:
            like = f"%{search}%"
            cond = or_(
                ResumeModel.title.ilike(like),
                ResumeModel.target_role.ilike(like),
                ResumeModel.summary.ilike(like),
            )
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)
        if domain:
            # JSONB contains the domain string as a list element (case-sensitive)
            stmt = stmt.where(ResumeModel.domains.contains([domain]))
            count_stmt = count_stmt.where(ResumeModel.domains.contains([domain]))
        if skill:
            stmt = stmt.where(
                or_(
                    ResumeModel.primary_skills.contains([skill]),
                    ResumeModel.secondary_skills.contains([skill]),
                )
            )
            count_stmt = count_stmt.where(
                or_(
                    ResumeModel.primary_skills.contains([skill]),
                    ResumeModel.secondary_skills.contains([skill]),
                )
            )
        stmt = stmt.order_by(ResumeModel.created_at.desc()).limit(limit).offset(offset)
        rows = (await self._session.execute(stmt)).scalars().all()
        total = (await self._session.execute(count_stmt)).scalar_one()
        return [_to_domain(r) for r in rows], total

    async def list_all_for_user(self, user_id: UUID) -> list[DomainResume]:
        stmt = select(ResumeModel).where(ResumeModel.user_id == user_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_domain(r) for r in rows]

    async def update(
        self,
        resume_id: UUID,
        *,
        user_id: UUID,
        fields: dict[str, object],
    ) -> DomainResume | None:
        stmt = select(ResumeModel).where(
            ResumeModel.id == resume_id, ResumeModel.user_id == user_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if not row:
            return None
        for k, v in fields.items():
            setattr(row, k, v)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _to_domain(row)

    async def delete(self, resume_id: UUID, *, user_id: UUID) -> bool:
        stmt = select(ResumeModel).where(
            ResumeModel.id == resume_id, ResumeModel.user_id == user_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if not row:
            return False
        await self._session.delete(row)
        await self._session.commit()
        return True
