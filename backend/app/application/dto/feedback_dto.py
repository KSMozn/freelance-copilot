"""DTOs for the in-app feedback + post-download survey surfaces."""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

FeedbackKind = Literal["general", "post_download"]


class GeneralFeedbackCreate(BaseModel):
    """Student-facing /feedback form.

    Trimmed to a floor of 10 chars to keep drive-by 'test' submissions
    out of the admin inbox — the frontend enforces the same rule.
    """

    message: str = Field(min_length=10, max_length=4000)


class SurveyCreate(BaseModel):
    """Post-download 1..5 star rating (+ optional short comment).

    template_slug is what the student was previewing when they clicked
    Download. Sent from the client (rather than looking it up server-
    side) so a rating always ties to the exact template that was
    downloaded, even if the student changes their default later.
    """

    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)
    template_slug: str | None = Field(default=None, max_length=64)


class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    kind: FeedbackKind
    rating: int | None
    message: str | None
    template_slug: str | None
    created_at: datetime
    resolved_at: datetime | None = None


class AdminFeedbackItem(BaseModel):
    """Feedback row enriched with author context for the admin triage inbox.

    Kept as a dedicated DTO (not `FeedbackRead`) so the student-facing
    surfaces never accidentally leak the user email/name of another
    student — this shape is only ever returned by /admin/feedback.
    """

    id: UUID
    user_id: UUID
    user_email: str | None
    user_full_name: str | None
    kind: FeedbackKind
    rating: int | None
    message: str | None
    template_slug: str | None
    created_at: datetime
    resolved_at: datetime | None
    resolved_by_email: str | None


class AdminFeedbackListResponse(BaseModel):
    items: list[AdminFeedbackItem]
    total: int
    unresolved_count: int


class FeedbackListResponse(BaseModel):
    items: list[FeedbackRead]
    total: int
