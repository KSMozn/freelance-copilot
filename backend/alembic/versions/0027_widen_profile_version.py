"""widen opportunity_scores.profile_version for persona stamps

Phase 2 sized this column for ``default-v1`` (10 chars). Phase C's
``PersonaProfileResolver`` writes ``persona:<uuid>`` (~44 chars) and
``user:<uuid>`` (~41 chars), both of which overflow VARCHAR(40). Job
analysis then 500s on every score insert.

Widen to VARCHAR(120) — matches ``match_reports.profile_version`` from
Phase E.

Revision ID: 0027_widen_profile_version
Revises: 0026_phase_h_tracker
Create Date: 2026-06-30
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0027_widen_profile_version"
down_revision = "0026_phase_h_tracker"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "opportunity_scores",
        "profile_version",
        existing_type=sa.String(length=40),
        type_=sa.String(length=120),
        existing_nullable=False,
    )


def downgrade() -> None:
    # Truncate to fit the old size so the downgrade is non-destructive on
    # rows written under Phase C.
    op.execute(
        "UPDATE opportunity_scores SET profile_version = LEFT(profile_version, 40) "
        "WHERE LENGTH(profile_version) > 40"
    )
    op.alter_column(
        "opportunity_scores",
        "profile_version",
        existing_type=sa.String(length=120),
        type_=sa.String(length=40),
        existing_nullable=False,
    )
