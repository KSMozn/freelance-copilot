"""Bundled CV templates the student can pick from in the wizard.

Rows are seeded by migration 0033 and correspond 1:1 to Jinja files under
`app/application/templates/student_cv/` — the `slug` is the source of
truth on both sides. Admins toggle `is_visible` + `sort_order` from the
admin panel; the DB is intentionally shallow so `display_name` /
`description` can be tuned via seed migrations without a manual UI edit.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class CvTemplate(Base):
    __tablename__ = "cv_templates"

    slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_visible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="100"
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
