"""phase B: knowledge graph core — experiences + projects

These tables hold the *facts* of a user's professional history that future
phases will project through persona lenses:

  * `experiences` — work history items (company, role, dates, summary).
    Populated from CV uploads (Phase D), LinkedIn PDF parsing (Phase D),
    or manual entry. Each experience can reference skills (via
    `experience_skills`) and achievements (via `experience_achievements`).
  * `projects` — discrete units of work. A project can come from a scanned
    repository (`origin = repo`), a manual portfolio entry
    (`origin = portfolio`), or be extracted from a CV (`origin = cv_extracted`).
    Same join-table pattern: `project_skills`, `project_achievements`.

`persona_id` / pinning lives in Phase C; this migration is purely additive
and does not modify any existing table.

Revision ID: 0017_phase_b_graph_core
Revises: 0016_phase_b_catalog_and_pot
Create Date: 2026-06-29
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0017_phase_b_graph_core"
down_revision = "0016_phase_b_catalog_and_pot"
branch_labels = None
depends_on = None


EXPERIENCE_SOURCES = ("cv", "linkedin", "manual", "backfill")
EMPLOYMENT_TYPES = ("full_time", "contract", "freelance", "internship", "part_time")
PROJECT_ORIGINS = ("repo", "portfolio", "cv_extracted", "manual")


def upgrade() -> None:
    op.create_table(
        "experiences",
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
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=160), nullable=True),
        sa.Column(
            "employment_type",
            sa.Enum(*EMPLOYMENT_TYPES, name="employment_type"),
            nullable=True,
        ),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),  # NULL = current
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "source",
            sa.Enum(*EXPERIENCE_SOURCES, name="experience_source"),
            nullable=False,
            server_default="manual",
        ),
        # Free-form reference to the originating record (cv_upload id,
        # linkedin_snapshot id, etc). Not an FK — sources vary by phase.
        sa.Column("source_ref", postgresql.UUID(as_uuid=True), nullable=True),
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

    op.create_table(
        "experience_skills",
        sa.Column(
            "experience_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("experiences.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "skill_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("skill_catalog.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("evidence_text", sa.Text(), nullable=True),
    )

    op.create_table(
        "experience_achievements",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "experience_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("experiences.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("metric_value", sa.Numeric(14, 2), nullable=True),
        sa.Column("metric_unit", sa.String(length=40), nullable=True),
        sa.Column("evidence_text", sa.Text(), nullable=True),
    )

    op.create_table(
        "projects",
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
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("role", sa.String(length=160), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column(
            "repo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "portfolio_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("portfolios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "origin",
            sa.Enum(*PROJECT_ORIGINS, name="project_origin"),
            nullable=False,
            server_default="manual",
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
    op.create_index("ix_projects_user_repo", "projects", ["user_id", "repo_id"])
    op.create_index(
        "ix_projects_user_portfolio", "projects", ["user_id", "portfolio_id"]
    )

    op.create_table(
        "project_skills",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "skill_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("skill_catalog.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("evidence_text", sa.Text(), nullable=True),
    )

    op.create_table(
        "project_achievements",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("metric_value", sa.Numeric(14, 2), nullable=True),
        sa.Column("metric_unit", sa.String(length=40), nullable=True),
        sa.Column("evidence_text", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("project_achievements")
    op.drop_table("project_skills")
    op.drop_index("ix_projects_user_portfolio", table_name="projects")
    op.drop_index("ix_projects_user_repo", table_name="projects")
    op.drop_table("projects")
    sa.Enum(name="project_origin").drop(op.get_bind(), checkfirst=True)

    op.drop_table("experience_achievements")
    op.drop_table("experience_skills")
    op.drop_table("experiences")
    sa.Enum(name="experience_source").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="employment_type").drop(op.get_bind(), checkfirst=True)
