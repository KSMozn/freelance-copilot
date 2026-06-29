from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, TimestampMixin, UUIDPKMixin


class Repository(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "repositories"
    __table_args__ = (
        UniqueConstraint("user_id", "github_url", name="uq_repositories_user_github_url"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    github_url: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    default_branch: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    languages: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    frameworks: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    libraries: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    databases: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    authentication: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    ai_providers: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    cloud: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    ci_systems: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    test_frameworks: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    has_docker: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_ci: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_tests: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    architecture_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_domain: Mapped[str | None] = mapped_column(String(120), nullable=True)
    strengths: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    highlights: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    readme_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)

    scan_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    scan_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    scanned_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)
    star_story: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    path_index: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
