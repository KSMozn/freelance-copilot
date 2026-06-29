"""SQLAlchemy models for Phase D ingestion surfaces.

Grouped in one module because they share the same lifecycle (uploaded by
the user, parsed by the LLM, ingested into the knowledge graph) and most
endpoints touch more than one of them.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CHAR,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base

PARSE_STATUSES = ("pending", "parsing", "parsed", "failed")
CONTENT_TYPES = ("blog_post", "talk", "paper", "open_source")


class UploadedFile(Base):
    """Generic blob registry.

    Used today by certificates + LinkedIn snapshots. CV uploads keep their
    own filename/sha columns because their lifecycle is tightly coupled to
    the parsing pipeline.
    """

    __tablename__ = "uploaded_files"
    __table_args__ = (
        UniqueConstraint("user_id", "sha256", name="uq_uploaded_files_user_sha"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CvUpload(Base):
    """A PDF / DOCX / pasted-text CV uploaded by the user.

    `extracted_text` is the raw text after PDF / DOCX extraction.
    `extracted_structure` is the LLM-structured JSON the
    `KnowledgeGraphService` will ingest. `parse_status` drives the UI's
    progress pill.
    """

    __tablename__ = "cv_uploads"
    __table_args__ = (
        UniqueConstraint("user_id", "sha256", name="uq_cv_uploads_user_sha"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    persona_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="SET NULL"),
        nullable=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parse_status: Mapped[str] = mapped_column(
        Enum(*PARSE_STATUSES, name="parse_status", create_type=False),
        nullable=False,
        default="pending",
    )
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_structure: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    extracted_skills: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    resume_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class LinkedInSnapshot(Base):
    """A parsed LinkedIn "Save to PDF" export.

    Same pipeline shape as `CvUpload` — text extraction → LLM structuring
    → graph ingest — but the dedicated table lets us specialize the
    structuring prompt (LinkedIn PDFs have a fairly consistent section
    layout) and surface "imported from LinkedIn" provenance in the UI.
    """

    __tablename__ = "linkedin_snapshots"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("uploaded_files.id", ondelete="SET NULL"),
        nullable=True,
    )
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_structure: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    parse_status: Mapped[str] = mapped_column(
        Enum(*PARSE_STATUSES, name="parse_status", create_type=False),
        nullable=False,
        default="pending",
    )
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuer: Mapped[str] = mapped_column(String(255), nullable=False)
    issued_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    credential_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    credential_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("uploaded_files.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ContentItem(Base):
    __tablename__ = "content_items"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        Enum(*CONTENT_TYPES, name="content_type", create_type=False),
        nullable=False,
        default="blog_post",
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
