"""phase L: CV template registry + student.cv_template_slug

Creates the `cv_templates` table (metadata for bundled Jinja templates
students pick from in the Preview step), adds a `cv_template_slug`
column to `student_profiles` for the student's saved choice, and seeds
the 5 templates we ship at launch.

Rows in `cv_templates` are seeded and never inserted via the UI — the
slug must match a physical Jinja file under
`backend/app/application/templates/student_cv/`. Admins can hide a
template (`is_visible = false`) or reorder via the admin panel.

Revision ID: 0033_phase_l_cv_templates
Revises: 0032_phase_k_student_dob
Create Date: 2026-07-01
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0033_phase_l_cv_templates"
down_revision = "0032_phase_k_student_dob"
branch_labels = None
depends_on = None


SEED_ROWS = [
    (
        "classic",
        "Classic",
        "Blue accents, header photo, and clear section dividers — the "
        "reliable default.",
        True,
        10,
    ),
    (
        "modern",
        "Modern",
        "Two-column layout with a left sidebar for contact + skills; "
        "main content on the right.",
        True,
        20,
    ),
    (
        "minimal",
        "Minimal",
        "Single-column, tight typography, no photo — clean and neutral.",
        True,
        30,
    ),
    (
        "academic",
        "Academic",
        "Serif type, education-first ordering — suits research and "
        "graduate applications.",
        True,
        40,
    ),
    (
        "creative",
        "Creative",
        "Colored header band, larger name, chip-style skills — for "
        "design-forward roles.",
        True,
        50,
    ),
]


def upgrade() -> None:
    op.create_table(
        "cv_templates",
        sa.Column("slug", sa.String(64), primary_key=True),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "is_visible",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default="100",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.add_column(
        "student_profiles",
        sa.Column("cv_template_slug", sa.String(64), nullable=True),
    )

    # Seed rows. Idempotent — safe to re-run against a partially-seeded
    # DB during development.
    templates_tbl = sa.table(
        "cv_templates",
        sa.column("slug", sa.String),
        sa.column("display_name", sa.String),
        sa.column("description", sa.Text),
        sa.column("is_visible", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )
    bind = op.get_bind()
    for slug, name, desc, visible, order in SEED_ROWS:
        exists = bind.execute(
            sa.text("SELECT 1 FROM cv_templates WHERE slug = :s"),
            {"s": slug},
        ).first()
        if exists:
            continue
        bind.execute(
            templates_tbl.insert().values(
                slug=slug,
                display_name=name,
                description=desc,
                is_visible=visible,
                sort_order=order,
            )
        )


def downgrade() -> None:
    op.drop_column("student_profiles", "cv_template_slug")
    op.drop_table("cv_templates")
