"""Portfolio CRUD + embedding-on-write side effects.

Every create / update generates a fresh embedding under the configured
provider's model. Embeddings under other models are left in place — they're
cheap to keep and disambiguate via the `model` column.
"""
from __future__ import annotations

from uuid import UUID

from app.application.dto.portfolio_dto import (
    PortfolioCreate,
    PortfolioListResponse,
    PortfolioRead,
    PortfolioUpdate,
)
from app.domain.entities.portfolio import Portfolio
from app.domain.exceptions import NotFoundError
from app.domain.providers.embedding_provider import EmbeddingProvider
from app.domain.repositories.embedding_repository import EmbeddingRepository
from app.domain.repositories.portfolio_repository import PortfolioRepository

PORTFOLIO_OWNER_TYPE = "portfolio"


def _to_read(p: Portfolio) -> PortfolioRead:
    return PortfolioRead(
        id=p.id,
        user_id=p.user_id,
        title=p.title,
        short_description=p.short_description,
        long_description=p.long_description,
        role=p.role,
        business_domain=p.business_domain,
        github_url=p.github_url,
        live_url=p.live_url,
        technologies=list(p.technologies),
        skills=list(p.skills),
        features=list(p.features),
        outcomes=list(p.outcomes),
        highlight=p.highlight,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


class PortfolioService:
    def __init__(
        self,
        *,
        portfolio_repo: PortfolioRepository,
        embedding_repo: EmbeddingRepository,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self._portfolios = portfolio_repo
        self._embeddings = embedding_repo
        self._provider = embedding_provider

    async def _embed_and_persist(self, portfolio: Portfolio) -> None:
        vector = await self._provider.embed(portfolio.embedding_text())
        await self._embeddings.upsert(
            owner_type=PORTFOLIO_OWNER_TYPE,
            owner_id=portfolio.id,
            model=self._provider.model_id,
            vector=vector,
        )

    async def create(self, user_id: UUID, payload: PortfolioCreate) -> PortfolioRead:
        portfolio = await self._portfolios.create(
            user_id=user_id,
            title=payload.title,
            short_description=payload.short_description,
            long_description=payload.long_description,
            role=payload.role,
            business_domain=payload.business_domain,
            github_url=str(payload.github_url) if payload.github_url else None,
            live_url=str(payload.live_url) if payload.live_url else None,
            technologies=list(payload.technologies),
            skills=list(payload.skills),
            features=list(payload.features),
            outcomes=list(payload.outcomes),
            highlight=payload.highlight,
        )
        await self._embed_and_persist(portfolio)
        return _to_read(portfolio)

    async def get(self, user_id: UUID, portfolio_id: UUID) -> PortfolioRead:
        portfolio = await self._portfolios.get_by_id(portfolio_id, user_id=user_id)
        if portfolio is None:
            raise NotFoundError("Portfolio not found")
        return _to_read(portfolio)

    async def list(
        self,
        user_id: UUID,
        *,
        search: str | None,
        domain: str | None,
        limit: int,
        offset: int,
    ) -> PortfolioListResponse:
        items, total = await self._portfolios.list_for_user(
            user_id, search=search, domain=domain, limit=limit, offset=offset
        )
        return PortfolioListResponse(
            items=[_to_read(p) for p in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update(
        self,
        user_id: UUID,
        portfolio_id: UUID,
        payload: PortfolioUpdate,
    ) -> PortfolioRead:
        fields: dict[str, object] = {}
        for k, v in payload.model_dump(exclude_unset=True).items():
            if k in ("github_url", "live_url") and v is not None:
                fields[k] = str(v)
            else:
                fields[k] = v

        if not fields:
            return await self.get(user_id, portfolio_id)

        portfolio = await self._portfolios.update(
            portfolio_id, user_id=user_id, fields=fields
        )
        if portfolio is None:
            raise NotFoundError("Portfolio not found")
        await self._embed_and_persist(portfolio)
        return _to_read(portfolio)

    async def delete(self, user_id: UUID, portfolio_id: UUID) -> None:
        existed = await self._portfolios.delete(portfolio_id, user_id=user_id)
        if not existed:
            raise NotFoundError("Portfolio not found")
        await self._embeddings.delete(
            owner_type=PORTFOLIO_OWNER_TYPE, owner_id=portfolio_id
        )

    async def ensure_embedding(self, portfolio: Portfolio) -> list[float]:
        """Used by the matching service to lazily embed portfolios that were
        created before the current embedding provider was selected.
        """
        existing = await self._embeddings.get(
            owner_type=PORTFOLIO_OWNER_TYPE,
            owner_id=portfolio.id,
            model=self._provider.model_id,
        )
        if existing is not None:
            return existing
        vector = await self._provider.embed(portfolio.embedding_text())
        await self._embeddings.upsert(
            owner_type=PORTFOLIO_OWNER_TYPE,
            owner_id=portfolio.id,
            model=self._provider.model_id,
            vector=vector,
        )
        return vector
