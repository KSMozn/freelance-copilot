from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, TimestampMixin, UUIDPKMixin


class Client(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "clients"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    total_spent: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    hire_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
