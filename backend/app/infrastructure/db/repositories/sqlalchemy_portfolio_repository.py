from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.portfolio import Portfolio as DomainPortfolio
from app.infrastructure.db.models.portfolio import Portfolio as PortfolioModel


def _to_domain(row: PortfolioModel) -> DomainPortfolio:
    return DomainPortfolio(
        id=row.id,
        user_id=row.user_id,
        title=row.title,
        short_description=row.short_description,
        long_description=row.long_description,
        role=row.role,
        business_domain=row.business_domain,
        github_url=row.github_url,
        live_url=row.live_url,
        technologies=list(row.technologies or []),
        skills=list(row.skills or []),
        features=list(row.features or []),
        outcomes=list(row.outcomes or []),
        highlight=row.highlight,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SQLAlchemyPortfolioRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: UUID,
        title: str,
        short_description: str | None,
        long_description: str,
        role: str | None,
        business_domain: str | None,
        github_url: str | None,
        live_url: str | None,
        technologies: list[str],
        skills: list[str],
        features: list[str],
        outcomes: list[str],
        highlight: bool,
    ) -> DomainPortfolio:
        row = PortfolioModel(
            user_id=user_id,
            title=title,
            short_description=short_description,
            long_description=long_description,
            role=role,
            business_domain=business_domain,
            github_url=github_url,
            live_url=live_url,
            technologies=technologies,
            skills=skills,
            features=features,
            outcomes=outcomes,
            highlight=highlight,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _to_domain(row)

    async def get_by_id(self, portfolio_id: UUID, *, user_id: UUID) -> DomainPortfolio | None:
        stmt = select(PortfolioModel).where(
            PortfolioModel.id == portfolio_id, PortfolioModel.user_id == user_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        search: str | None,
        domain: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[DomainPortfolio], int]:
        stmt = select(PortfolioModel).where(PortfolioModel.user_id == user_id)
        count_stmt = select(func.count(PortfolioModel.id)).where(
            PortfolioModel.user_id == user_id
        )
        if domain:
            stmt = stmt.where(PortfolioModel.business_domain.ilike(f"%{domain}%"))
            count_stmt = count_stmt.where(PortfolioModel.business_domain.ilike(f"%{domain}%"))
        if search:
            like = f"%{search}%"
            cond = or_(
                PortfolioModel.title.ilike(like),
                PortfolioModel.long_description.ilike(like),
                PortfolioModel.short_description.ilike(like),
            )
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)
        stmt = (
            stmt.order_by(PortfolioModel.highlight.desc(), PortfolioModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        total = (await self._session.execute(count_stmt)).scalar_one()
        return [_to_domain(r) for r in rows], total

    async def list_all_for_user(self, user_id: UUID) -> list[DomainPortfolio]:
        stmt = select(PortfolioModel).where(PortfolioModel.user_id == user_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_domain(r) for r in rows]

    async def update(
        self,
        portfolio_id: UUID,
        *,
        user_id: UUID,
        fields: dict[str, object],
    ) -> DomainPortfolio | None:
        stmt = select(PortfolioModel).where(
            PortfolioModel.id == portfolio_id, PortfolioModel.user_id == user_id
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

    async def delete(self, portfolio_id: UUID, *, user_id: UUID) -> bool:
        stmt = select(PortfolioModel).where(
            PortfolioModel.id == portfolio_id, PortfolioModel.user_id == user_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if not row:
            return False
        await self._session.delete(row)
        await self._session.commit()
        return True
