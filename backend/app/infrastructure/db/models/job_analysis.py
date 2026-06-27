from typing import Any
from uuid import UUID

from sqlalchemy import (
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, TimestampMixin, UUIDPKMixin

ComplexityEnum = SAEnum("low", "medium", "high", name="complexity_level", create_type=True)
RiskEnum = SAEnum("low", "medium", "high", name="risk_level", create_type=True)


class JobAnalysis(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "job_analyses"
    __table_args__ = (UniqueConstraint("job_id", name="uq_job_analyses_job_id"),)

    job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    required_skills: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    preferred_skills: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    seniority: Mapped[str | None] = mapped_column(String(50), nullable=True)
    business_domain: Mapped[str | None] = mapped_column(String(120), nullable=True)
    complexity: Mapped[str | None] = mapped_column(ComplexityEnum, nullable=True)
    hidden_requirements: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    technologies: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    expected_deliverables: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    estimated_hours_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_hours_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(RiskEnum, nullable=True)
    communication_required: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Phase-2 additions
    budget_assessment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    client_intent: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    risks: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    red_flags: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    green_flags: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    questions_to_ask_client: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    prompt_version: Mapped[str | None] = mapped_column(String(40), nullable=True)

    raw_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
