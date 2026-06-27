from typing import Protocol
from uuid import UUID

from app.domain.entities.portfolio import Portfolio


class PortfolioRepository(Protocol):
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
    ) -> Portfolio: ...

    async def get_by_id(self, portfolio_id: UUID, *, user_id: UUID) -> Portfolio | None: ...

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        search: str | None,
        domain: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Portfolio], int]: ...

    async def list_all_for_user(self, user_id: UUID) -> list[Portfolio]: ...

    async def update(
        self,
        portfolio_id: UUID,
        *,
        user_id: UUID,
        fields: dict[str, object],
    ) -> Portfolio | None: ...

    async def delete(self, portfolio_id: UUID, *, user_id: UUID) -> bool: ...
