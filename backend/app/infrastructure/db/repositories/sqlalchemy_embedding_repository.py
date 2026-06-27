from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.embedding import EMBEDDING_DIM, Embedding


class SQLAlchemyEmbeddingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self,
        *,
        owner_type: str,
        owner_id: UUID,
        model: str,
    ) -> list[float] | None:
        stmt = select(Embedding.vector).where(
            Embedding.owner_type == owner_type,
            Embedding.owner_id == owner_id,
            Embedding.model == model,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        # pgvector returns numpy arrays or lists depending on driver setup
        return [float(x) for x in row]

    async def upsert(
        self,
        *,
        owner_type: str,
        owner_id: UUID,
        model: str,
        vector: list[float],
    ) -> None:
        if len(vector) != EMBEDDING_DIM:
            raise ValueError(
                f"Embedding dim mismatch: got {len(vector)}, expected {EMBEDDING_DIM}"
            )
        stmt = pg_insert(Embedding).values(
            owner_type=owner_type,
            owner_id=owner_id,
            model=model,
            dim=len(vector),
            vector=vector,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_embedding_owner_model",
            set_={"vector": vector, "dim": len(vector)},
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def get_many(
        self,
        *,
        owner_type: str,
        owner_ids: list[UUID],
        model: str,
    ) -> dict[UUID, list[float]]:
        if not owner_ids:
            return {}
        stmt = select(Embedding.owner_id, Embedding.vector).where(
            Embedding.owner_type == owner_type,
            Embedding.model == model,
            Embedding.owner_id.in_(owner_ids),
        )
        rows = (await self._session.execute(stmt)).all()
        return {row[0]: [float(x) for x in row[1]] for row in rows}

    async def delete(self, *, owner_type: str, owner_id: UUID) -> None:
        from sqlalchemy import delete as sa_delete

        await self._session.execute(
            sa_delete(Embedding).where(
                Embedding.owner_type == owner_type, Embedding.owner_id == owner_id
            )
        )
        await self._session.commit()
