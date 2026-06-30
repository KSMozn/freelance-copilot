"""phase K: student persona — wizard-driven CV builder

The Student persona is a deliberately simpler surface than the rest of the
platform: a single-form, step-by-step wizard captures basic info, education,
photo, skills, courses, projects, volunteer work, languages, and
certificates, then produces a downloadable PDF CV. Students don't see jobs,
match reports, proposals, applications — only the wizard, their profile,
and their CV.

This migration adds:

  * `users.selected_persona_kind` — picked at registration. Routes the user
    on first login: "student" → wizard, anything else → existing app.
  * `student_profiles` — 1:1 with user, holds the wizard's "Basics +
    Education + Photo + Summary" payload plus wizard progress markers.
  * `student_profile_entries` — repeating items (courses, projects,
    volunteer work, certificates, skills, awards, extracurriculars). One
    table with a `kind` discriminator + flexible `details` JSONB keeps the
    schema small while letting each kind carry its own extras.

It also seeds a `student` row into `persona_archetypes` so the existing
PersonaService can instantiate a Student persona for the user without any
special-casing.

Revision ID: 0028_phase_k_student_persona
Revises: 0027_widen_profile_version
Create Date: 2026-06-30
"""
from __future__ import annotations

import json

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0028_phase_k_student_persona"
down_revision = "0027_widen_profile_version"
branch_labels = None
depends_on = None


# Persona kinds picked at registration. "professional" is the default for
# every existing user (set by the data step below). New kinds added later
# (e.g. "career_changer") just extend this list — the column is varchar so
# no enum migration churn.
PERSONA_KINDS = ("professional", "student")

# Entry kinds. One table per kind would be cleaner but each kind has the
# same shape: title + organization + dates + description + a small extras
# blob. The discriminator + JSONB keeps the surface area tight and the CV
# renderer's job trivial (group_by kind, sort, render).
STUDENT_ENTRY_KINDS = (
    "course",
    "project",
    "volunteer",
    "certificate",
    "skill",
    "award",
    "extracurricular",
    "language",
)


def upgrade() -> None:
    # -------- users.selected_persona_kind ------------------------------
    # Default "professional" so every existing row keeps its current
    # behaviour. New registrations write the chosen kind explicitly.
    op.add_column(
        "users",
        sa.Column(
            "selected_persona_kind",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'professional'"),
        ),
    )
    op.create_index(
        "ix_users_persona_kind", "users", ["selected_persona_kind"]
    )

    # -------- student_profiles ----------------------------------------
    op.create_table(
        "student_profiles",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        # "Basics" step
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("professional_email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        # "Education" step
        sa.Column("college", sa.String(length=255), nullable=True),
        sa.Column("degree", sa.String(length=120), nullable=True),
        sa.Column("major", sa.String(length=255), nullable=True),
        sa.Column("graduation_year", sa.SmallInteger(), nullable=True),
        sa.Column("gpa", sa.Numeric(precision=3, scale=2), nullable=True),
        # "Photo" step — nullable; the wizard explicitly tells students it's
        # optional. Stored via the existing uploaded_files registry.
        sa.Column(
            "photo_file_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("uploaded_files.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # "Summary" step
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("headline", sa.String(length=255), nullable=True),
        # "Links" sub-step (github / linkedin / website / portfolio)
        sa.Column(
            "links",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "interests",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        # Wizard progress. Each step's slug goes into `completed_steps` on
        # save; `current_step` lets us land returning users back where they
        # left off. The frontend stays the source of truth on order — these
        # are just markers.
        sa.Column(
            "completed_steps",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("current_step", sa.String(length=64), nullable=True),
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

    # -------- student_profile_entries ---------------------------------
    op.create_table(
        "student_profile_entries",
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
        ),
        sa.Column(
            "kind",
            sa.Enum(*STUDENT_ENTRY_KINDS, name="student_entry_kind"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("organization", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "is_current", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=512), nullable=True),
        # Kind-specific extras. Examples:
        #   course: {grade, credits, semester}
        #   project: {tech_stack: [...], role}
        #   skill: {category, proficiency: 1-5}
        #   certificate: {issuer, credential_id}
        #   language: {proficiency: "basic|intermediate|fluent|native"}
        sa.Column(
            "details",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "sort_order", sa.SmallInteger(), nullable=False, server_default="0"
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
    op.create_index(
        "ix_student_entries_user_kind",
        "student_profile_entries",
        ["user_id", "kind", "sort_order"],
    )

    # -------- seed Student persona archetype --------------------------
    # The Student archetype is a *real* archetype row so existing
    # PersonaService.instantiate_from_archetype(slug=...) can spin up the
    # user's persona at registration with no special-casing. The scoring
    # weights are irrelevant for students (they don't run job analyses)
    # but we set sensible defaults so the row is well-formed.
    default_weights = {
        "technical_fit": 30,
        "domain_fit": 10,
        "proposal_count": 10,
        "budget_attractiveness": 10,
        "client_quality": 10,
        "estimated_effort": 10,
        "risk_level": 10,
        "strategic_value": 10,
    }
    default_skill_category_weights = {
        "language": 0.25,
        "framework": 0.20,
        "tool": 0.15,
        "practice": 0.15,
        "soft": 0.15,
        "domain": 0.10,
    }
    # `default_proposal_tone` is a Postgres enum (`proposal_tone`) created
    # by migration 0020. The driver passes our string parameter as VARCHAR,
    # so we cast it explicitly to the enum type to avoid DatatypeMismatch.
    op.execute(
        sa.text(
            """
            INSERT INTO persona_archetypes (
                slug, name, description,
                default_weights, default_skill_category_weights,
                default_proposal_tone, default_target_roles,
                default_seniority_band, is_active, sort_order
            ) VALUES (
                :slug, :name, :description,
                CAST(:default_weights AS JSONB),
                CAST(:default_skill_category_weights AS JSONB),
                CAST(:default_proposal_tone AS proposal_tone),
                CAST(:default_target_roles AS JSONB),
                :default_seniority_band, true, :sort_order
            )
            ON CONFLICT (slug) DO NOTHING
            """
        ).bindparams(
            slug="student",
            name="Student",
            description=(
                "University / college student building a first CV. Optimised for "
                "guided onboarding: a step-by-step wizard captures education, "
                "skills, courses, projects, volunteer work, and certifications, "
                "then renders a downloadable PDF."
            ),
            default_weights=json.dumps(default_weights),
            default_skill_category_weights=json.dumps(
                default_skill_category_weights
            ),
            default_proposal_tone="pragmatic",
            default_target_roles=json.dumps(
                [
                    "Intern",
                    "Junior Software Engineer",
                    "Graduate Engineer",
                    "Working Student",
                ]
            ),
            default_seniority_band="entry",
            sort_order=100,  # last in the gallery
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM persona_archetypes WHERE slug = 'student'")
    )
    op.drop_index(
        "ix_student_entries_user_kind", table_name="student_profile_entries"
    )
    op.drop_table("student_profile_entries")
    sa.Enum(name="student_entry_kind").drop(op.get_bind(), checkfirst=True)
    op.drop_table("student_profiles")
    op.drop_index("ix_users_persona_kind", table_name="users")
    op.drop_column("users", "selected_persona_kind")
