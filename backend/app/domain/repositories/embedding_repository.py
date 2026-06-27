from typing import Protocol
from uuid import UUID


class EmbeddingRepository(Protocol):
    """Polymorphic store for owner→vector embeddings.

    `owner_type` is a short string like 'portfolio' or 'job'. `model` includes
    the provider so two providers with the same nominal model name (e.g.
    OpenAI's text-embedding-3-small vs. a mock with 1536 dims) never collide.
    """

    async def get(
        self,
        *,
        owner_type: str,
        owner_id: UUID,
        model: str,
    ) -> list[float] | None: ...

    async def upsert(
        self,
        *,
        owner_type: str,
        owner_id: UUID,
        model: str,
        vector: list[float],
    ) -> None: ...

    async def get_many(
        self,
        *,
        owner_type: str,
        owner_ids: list[UUID],
        model: str,
    ) -> dict[UUID, list[float]]: ...

    async def delete(self, *, owner_type: str, owner_id: UUID) -> None: ...
