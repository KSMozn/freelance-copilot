from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, TimestampMixin, UUIDPKMixin

EMBEDDING_DIM = 1536


class Embedding(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "embeddings"
    __table_args__ = (
        UniqueConstraint("owner_type", "owner_id", "model", name="uq_embedding_owner_model"),
        Index(
            "ix_embeddings_vector_cosine",
            "vector",
            postgresql_using="ivfflat",
            postgresql_ops={"vector": "vector_cosine_ops"},
            postgresql_with={"lists": 100},
        ),
    )

    owner_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    owner_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    dim: Mapped[int] = mapped_column(Integer, nullable=False, default=EMBEDDING_DIM)
    vector: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
