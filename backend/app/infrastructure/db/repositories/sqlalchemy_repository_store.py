from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.repository import (
    Repository as DomainRepository,
)
from app.domain.entities.repository import (
    StarStory,
)
from app.infrastructure.db.models.repository import Repository as RepositoryModel


def _star_from_jsonb(raw: dict | None) -> StarStory | None:
    if not isinstance(raw, dict):
        return None
    if not raw.get("headline") and not raw.get("action"):
        return None
    return StarStory(
        headline=str(raw.get("headline", "")),
        situation=str(raw.get("situation", "")),
        task=str(raw.get("task", "")),
        action=str(raw.get("action", "")),
        result=str(raw.get("result", "")),
    )


def _star_to_jsonb(story: StarStory | None) -> dict | None:
    if story is None:
        return None
    return {
        "headline": story.headline,
        "situation": story.situation,
        "task": story.task,
        "action": story.action,
        "result": story.result,
    }


def _to_domain(row: RepositoryModel) -> DomainRepository:
    return DomainRepository(
        id=row.id,
        user_id=row.user_id,
        github_url=row.github_url,
        owner=row.owner,
        name=row.name,
        default_branch=row.default_branch,
        description=row.description,
        languages=dict(row.languages or {}),
        frameworks=list(row.frameworks or []),
        libraries=list(row.libraries or []),
        databases=list(row.databases or []),
        authentication=list(row.authentication or []),
        ai_providers=list(row.ai_providers or []),
        cloud=list(row.cloud or []),
        ci_systems=list(row.ci_systems or []),
        test_frameworks=list(row.test_frameworks or []),
        has_docker=row.has_docker,
        has_ci=row.has_ci,
        has_tests=row.has_tests,
        architecture_summary=row.architecture_summary,
        business_domain=row.business_domain,
        strengths=list(row.strengths or []),
        highlights=list(row.highlights or []),
        readme_excerpt=row.readme_excerpt,
        scan_status=row.scan_status,
        scan_error=row.scan_error,
        scanned_at=row.scanned_at,
        star_story=_star_from_jsonb(row.star_story),
        path_index=[str(p) for p in (row.path_index or []) if p],
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SQLAlchemyRepositoryStore:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: UUID,
        github_url: str,
        owner: str,
        name: str,
    ) -> DomainRepository:
        row = RepositoryModel(
            user_id=user_id,
            github_url=github_url,
            owner=owner,
            name=name,
            scan_status="pending",
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _to_domain(row)

    async def get_by_id(self, repository_id: UUID, *, user_id: UUID) -> DomainRepository | None:
        stmt = select(RepositoryModel).where(
            RepositoryModel.id == repository_id, RepositoryModel.user_id == user_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def get_by_github_url(
        self, github_url: str, *, user_id: UUID
    ) -> DomainRepository | None:
        stmt = select(RepositoryModel).where(
            RepositoryModel.user_id == user_id, RepositoryModel.github_url == github_url
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[DomainRepository], int]:
        stmt = select(RepositoryModel).where(RepositoryModel.user_id == user_id)
        count_stmt = select(func.count(RepositoryModel.id)).where(
            RepositoryModel.user_id == user_id
        )
        if search:
            like = f"%{search}%"
            cond = or_(
                RepositoryModel.name.ilike(like),
                RepositoryModel.owner.ilike(like),
                RepositoryModel.description.ilike(like),
                RepositoryModel.architecture_summary.ilike(like),
            )
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)
        stmt = stmt.order_by(RepositoryModel.created_at.desc()).limit(limit).offset(offset)
        rows = (await self._session.execute(stmt)).scalars().all()
        total = (await self._session.execute(count_stmt)).scalar_one()
        return [_to_domain(r) for r in rows], total

    async def list_all_for_user(self, user_id: UUID) -> list[DomainRepository]:
        stmt = select(RepositoryModel).where(RepositoryModel.user_id == user_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_domain(r) for r in rows]

    async def update(
        self,
        repository_id: UUID,
        *,
        user_id: UUID,
        fields: dict[str, object],
    ) -> DomainRepository | None:
        stmt = select(RepositoryModel).where(
            RepositoryModel.id == repository_id, RepositoryModel.user_id == user_id
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

    async def delete(self, repository_id: UUID, *, user_id: UUID) -> bool:
        stmt = select(RepositoryModel).where(
            RepositoryModel.id == repository_id, RepositoryModel.user_id == user_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if not row:
            return False
        await self._session.delete(row)
        await self._session.commit()
        return True
