from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, TimestampMixin, UUIDPKMixin

# The 'draft' and 'offer' values are added by migration 0006. SQLAlchemy
# is told to NOT create the type (Phase-1 created it).
ApplicationStatusEnum = SAEnum(
    "applied",
    "viewed",
    "interview",
    "rejected",
    "won",
    "completed",
    "withdrawn",
    "draft",
    "offer",
    name="application_status",
    create_type=False,
)


class Application(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "applications"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    proposal_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("proposals.id", ondelete="SET NULL"),
        nullable=True,
    )
    resume_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Phase H — exact Output rows that were sent. NULL on rows created
    # before Phase F or applications where the user typed their own text.
    resume_output_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("outputs.id", ondelete="SET NULL"),
        nullable=True,
    )
    cover_letter_output_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("outputs.id", ondelete="SET NULL"),
        nullable=True,
    )
    portfolio_ids: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    status: Mapped[str] = mapped_column(
        ApplicationStatusEnum, nullable=False, default="applied", index=True
    )

    # per-status timestamps
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    interview_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    offer_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    won_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    contract_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    client_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # immutable record of the inputs at submission time
    snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class ApplicationHistory(Base, UUIDPKMixin):
    __tablename__ = "application_history"

    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    from_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    to_status: Mapped[str] = mapped_column(String(40), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ApplicationPortfolio(Base):
    """Legacy m2m kept around for Phase-1 compatibility. Not used in Phase 6 —
    portfolios applied with the proposal live in `applications.portfolio_ids`
    so the snapshot stays self-contained.
    """

    __tablename__ = "application_portfolios"

    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        primary_key=True,
    )
    portfolio_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
