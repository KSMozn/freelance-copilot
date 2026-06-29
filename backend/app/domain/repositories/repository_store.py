"""Persistence port for scanned code repositories.

Named `RepositoryStore` rather than `RepositoryRepository` to avoid the
double-up — the entity is `Repository`, so `…Repository.repository(…)`
would read like a stutter.
"""
from typing import Protocol
from uuid import UUID

from app.domain.entities.repository import Repository


class RepositoryStore(Protocol):
    async def create(
        self,
        *,
        user_id: UUID,
        github_url: str,
        owner: str,
        name: str,
    ) -> Repository: ...

    async def get_by_id(self, repository_id: UUID, *, user_id: UUID) -> Repository | None: ...

    async def get_by_github_url(self, github_url: str, *, user_id: UUID) -> Repository | None: ...

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Repository], int]: ...

    async def list_all_for_user(self, user_id: UUID) -> list[Repository]: ...

    async def update(
        self,
        repository_id: UUID,
        *,
        user_id: UUID,
        fields: dict[str, object],
    ) -> Repository | None: ...

    async def delete(self, repository_id: UUID, *, user_id: UUID) -> bool: ...
