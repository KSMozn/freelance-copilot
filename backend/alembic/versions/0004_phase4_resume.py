"""phase 4: resume library

Reshapes the Phase-1 placeholder resumes table to the Phase-4 contract:
- label → title
- drops content, file_url, is_default (file upload + default-resume rule are
  out of Phase-4 scope; recommendations replace the "default" concept)
- adds target_role, summary, seniority_level, primary/secondary_skills,
  industries, domains, achievements, project_highlights, keywords, notes

Revision ID: 0004_phase4_resume
Revises: 0003_phase3_portfolio
Create Date: 2026-06-28
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0004_phase4_resume"
down_revision = "0003_phase3_portfolio"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("resumes", "label", new_column_name="title")
    op.drop_column("resumes", "content")
    op.drop_column("resumes", "file_url")
    op.drop_column("resumes", "is_default")

    op.add_column("resumes", sa.Column("target_role", sa.String(160), nullable=True))
    op.add_column("resumes", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("resumes", sa.Column("seniority_level", sa.String(40), nullable=True))
    op.add_column(
        "resumes",
        sa.Column("primary_skills", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "resumes",
        sa.Column("secondary_skills", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "resumes",
        sa.Column("industries", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "resumes",
        sa.Column("domains", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "resumes",
        sa.Column("achievements", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "resumes",
        sa.Column("project_highlights", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "resumes",
        sa.Column("keywords", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column("resumes", sa.Column("notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("resumes", "notes")
    op.drop_column("resumes", "keywords")
    op.drop_column("resumes", "project_highlights")
    op.drop_column("resumes", "achievements")
    op.drop_column("resumes", "domains")
    op.drop_column("resumes", "industries")
    op.drop_column("resumes", "secondary_skills")
    op.drop_column("resumes", "primary_skills")
    op.drop_column("resumes", "seniority_level")
    op.drop_column("resumes", "summary")
    op.drop_column("resumes", "target_role")

    op.add_column(
        "resumes",
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("resumes", sa.Column("file_url", sa.Text(), nullable=True))
    op.add_column(
        "resumes",
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
    )
    op.alter_column("resumes", "title", new_column_name="label")
