"""SQLAlchemy models for the Student persona's wizard-driven CV builder.

Two tables back the entire surface:

  * `StudentProfile` (1:1 with user) — the "Basics + Education + Photo +
    Summary + Links" payload + wizard progress markers. The user_id is the
    primary key because each user has at most one student profile.
  * `StudentProfileEntry` — repeating items the student adds (courses,
    projects, volunteer work, certificates, awards, skills, languages,
    extracurriculars). One table with a `kind` discriminator + flexible
    `details` JSONB keeps the schema small. The CV renderer groups by kind
    and sorts by `sort_order` to draw the sections.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base

# Mirror of the enum created in migration 0028. Keep in lockstep.
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


class StudentProfile(Base):
    """One row per student, keyed by user_id.

    The wizard writes step-by-step: every step's slug lands in
    `completed_steps` on save, and `current_step` lets us drop returning
    students back where they left off. The CV renderer treats missing
    fields as "skip this line" rather than blocking — partial profiles
    still produce a CV.
    """

    __tablename__ = "student_profiles"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Basics
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    professional_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Education
    college: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department: Mapped[str | None] = mapped_column(String(200), nullable=True)
    degree: Mapped[str | None] = mapped_column(String(120), nullable=True)
    major: Mapped[str | None] = mapped_column(String(255), nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    gpa: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)

    # Photo — nullable; the wizard tells students it's optional.
    photo_file_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("uploaded_files.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Crop transform applied at display time only — the on-disk bytes
    # are never modified. Offsets are 0-100 percentages fed into CSS
    # `background-position`; zoom is 100-300 fed into `background-size`.
    # Defaults (50/50/100) produce the natural "centered, fitted" crop.
    photo_offset_x: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=50, server_default="50"
    )
    photo_offset_y: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=50, server_default="50"
    )
    photo_zoom: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=100, server_default="100"
    )

    # Summary
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    headline: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Links: {"github": "...", "linkedin": "...", "website": "...",
    # "portfolio": "..."}
    links: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    interests: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )

    # Career Starter Pack — generated LinkedIn/GitHub content + review
    # recommendations. See migration 0036 for schema notes. All keys are
    # optional; empty dict means the student has not opened either card yet.
    career_pack: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=sa.text("'{}'::jsonb")
    )

    # Wizard progress
    completed_steps: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    current_step: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # CV template selection. Slug matches a row in cv_templates + a Jinja
    # file under templates/student_cv/. Null → resolver falls back to the
    # first visible template. No FK to cv_templates so admins can delete
    # templates without student-row constraint headaches.
    cv_template_slug: Mapped[str | None] = mapped_column(
        String(64), nullable=True
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


class StudentProfileEntry(Base):
    """Repeating wizard items (course / project / volunteer / …).

    `details` carries kind-specific extras so the table stays narrow:
      * course: {grade, credits, semester}
      * project: {tech_stack: [..], role}
      * skill: {category, proficiency: 1-5}
      * certificate: {issuer, credential_id}
      * language: {proficiency: "basic|intermediate|fluent|native"}
    The renderer reads `details` per-kind; the API accepts any JSON object.
    """

    __tablename__ = "student_profile_entries"
    __table_args__ = (
        Index(
            "ix_student_entries_user_kind",
            "user_id",
            "kind",
            "sort_order",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(
        Enum(*STUDENT_ENTRY_KINDS, name="student_entry_kind", create_type=False),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    sort_order: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0
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
