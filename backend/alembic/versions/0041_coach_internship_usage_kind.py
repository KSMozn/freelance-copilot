"""Add `coach.internship` to usage_event_kind enum.

Emitted by the new POST /students/coach/internship endpoint. Meta
carries the industry preset the student picked, whether the LLM
returned follow-ups (vague), and how many bullets it produced.
"""
from alembic import op

revision = "0041_coach_internship_usage_kind"
down_revision = "0040_add_internship_entry_kind"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE usage_event_kind ADD VALUE IF NOT EXISTS 'coach.internship'")


def downgrade() -> None:
    pass
