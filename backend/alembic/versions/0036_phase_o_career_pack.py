"""Phase O — career_pack JSONB on student_profiles

Holds the generated LinkedIn / GitHub content + review recommendations
for the post-CV Career Starter Pack page. One column instead of ten so
the shape can evolve without another migration each time.

Structure (all keys optional):

    {
      "linkedin_status": "missing|started|needs_improvement|completed",
      "github_status":   "missing|started|needs_improvement|completed",
      "linkedin_generated":     { headline, about, education, projects, skills, checklist },
      "linkedin_recommendations": { ... review payload ... },
      "linkedin_profile_text":  "…last pasted profile text…",
      "github_generated":       { username_suggestions, bio, profile_readme, project_readmes, checklist },
      "github_recommendations": { ... review payload ... },
      "github_username":        "…"
    }

The linkedin/github URLs stay in the existing `links` JSONB — this
column is only for generated content and review state.
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0036_phase_o_career_pack"
down_revision = "0035_phase_n_photo_transform"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_profiles",
        sa.Column(
            "career_pack",
            JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("student_profiles", "career_pack")
