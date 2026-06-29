"""phase D: source ingestion tables

Adds the five tables that hold "raw material" coming in from outside the
codebase, plus the structured extractions derived from each:

  * `uploaded_files` — generic blob registry (used by certificates and
    LinkedIn snapshots, and future surfaces). Dedups by (user_id, sha256).
  * `cv_uploads` — PDF / DOCX / pasted-text CV uploads. Carries the
    extracted text, the parse_status, and the LLM-structured JSON
    (experiences[], skills[], achievements[]) that `KnowledgeGraphService`
    ingests into the per-user graph.
  * `linkedin_snapshots` — same flow but for LinkedIn "Save to PDF" exports.
    Keeps its own table so we can ship LinkedIn-specific parsers / prompts
    later without disturbing CV ingestion.
  * `certificates` — manual entries (name, issuer, dates, credential_id /
    URL) with an optional file attachment.
  * `content_items` — published work (blog post, talk, paper, open-source
    project). URL-only is fine; raw_text optional.

Revision ID: 0023_phase_d_ingestion
Revises: 0022_phase_c_backfill_primary
Create Date: 2026-06-29
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0023_phase_d_ingestion"
down_revision = "0022_phase_c_backfill_primary"
branch_labels = None
depends_on = None


PARSE_STATUSES = ("pending", "parsing", "parsed", "failed")
CONTENT_TYPES = ("blog_post", "talk", "paper", "open_source")


def upgrade() -> None:
    # ---- generic blob registry ----------------------------------------
    op.create_table(
        "uploaded_files",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("sha256", sa.CHAR(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "sha256", name="uq_uploaded_files_user_sha"),
    )

    # ---- CV uploads ----------------------------------------------------
    op.create_table(
        "cv_uploads",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "persona_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("personas.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=True),
        sa.Column("sha256", sa.CHAR(length=64), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column(
            "parse_status",
            sa.Enum(*PARSE_STATUSES, name="parse_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("parse_error", sa.Text(), nullable=True),
        sa.Column(
            "extracted_structure",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "extracted_skills",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "resume_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "sha256", name="uq_cv_uploads_user_sha"),
    )

    # ---- LinkedIn snapshots --------------------------------------------
    op.create_table(
        "linkedin_snapshots",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "file_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("uploaded_files.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column(
            "extracted_structure",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "parse_status",
            sa.Enum(*PARSE_STATUSES, name="parse_status", create_type=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("parse_error", sa.Text(), nullable=True),
        sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ---- Certificates --------------------------------------------------
    op.create_table(
        "certificates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("issuer", sa.String(length=255), nullable=False),
        sa.Column("issued_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("credential_id", sa.String(length=255), nullable=True),
        sa.Column("credential_url", sa.Text(), nullable=True),
        sa.Column(
            "file_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("uploaded_files.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # ---- Content items (blog posts / talks / papers / OSS) -------------
    op.create_table(
        "content_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "type",
            sa.Enum(*CONTENT_TYPES, name="content_type"),
            nullable=False,
            server_default="blog_post",
        ),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("published_date", sa.Date(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("content_items")
    sa.Enum(name="content_type").drop(op.get_bind(), checkfirst=True)
    op.drop_table("certificates")
    op.drop_table("linkedin_snapshots")
    op.drop_table("cv_uploads")
    sa.Enum(name="parse_status").drop(op.get_bind(), checkfirst=True)
    op.drop_table("uploaded_files")
