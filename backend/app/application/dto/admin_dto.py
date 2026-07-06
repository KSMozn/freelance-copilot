"""DTOs for the admin panel — /api/v1/admin/*.

Two groupings:
  * Aggregates (Overview): totals, wizard funnel counts, entries by kind,
    signups time series.
  * Records (Users / Activity): paginated lists and a rich user detail.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ---- Overview -----------------------------------------------------------


class SignupsPoint(BaseModel):
    day: date
    count: int


class WizardFunnel(BaseModel):
    """Per-step count of students who reached each wizard step. The step
    strings match the frontend's STEPS array slugs.
    """

    registered: int
    basics: int
    education: int
    photo: int
    skills: int
    courses: int
    projects: int
    internships: int = 0
    volunteer: int
    languages: int
    certificates: int
    summary: int
    preview: int
    starter_pack: int = 0
    downloaded: int


class EntryKindCount(BaseModel):
    kind: str
    count: int


class UsageKindCount(BaseModel):
    kind: str
    count: int
    errors: int


class AdminOverview(BaseModel):
    users_total: int
    users_students: int
    users_active_7d: int
    signups_today: int
    signups_7d: int
    signups_30d: int
    signups_series: list[SignupsPoint]
    funnel: WizardFunnel
    entries_by_kind: list[EntryKindCount]
    usage_by_kind_7d: list[UsageKindCount]


# ---- Users --------------------------------------------------------------


class AdminUserRow(BaseModel):
    """One row in the admin users table. Compact — full detail is behind
    a per-user endpoint.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None
    persona_kind: str
    is_active: bool
    is_superuser: bool
    email_verified: bool
    last_login_at: datetime | None
    created_at: datetime
    wizard_step: str | None  # student profile's current_step, if any
    wizard_completed: int  # count of completed_steps
    # Derived from the CV's links field (entered in the wizard basics step),
    # NOT from the Career Starter Pack step. `null` if the user has no
    # student_profile row (no CV wizard progress at all).
    has_linkedin: bool | None = None
    has_github: bool | None = None
    # True if there's any successful `cv.pdf` usage_event for this user.
    has_downloaded_cv: bool | None = None


class AdminUserListResponse(BaseModel):
    items: list[AdminUserRow]
    total: int
    page: int
    size: int


class AdminStudentSummary(BaseModel):
    """The student profile portion shown on the user detail page.

    Not exposed unless the user is a student; keeps the detail page
    tight for non-student accounts.
    """

    full_name: str | None
    professional_email: str | None
    phone: str | None
    location: str | None
    date_of_birth: date | None
    college: str | None
    department: str | None
    degree: str | None
    major: str | None
    graduation_year: int | None
    gpa: str | None
    headline: str | None
    summary: str | None
    links: dict[str, Any]
    interests: list[Any]
    completed_steps: list[str]
    current_step: str | None
    cv_template_slug: str | None
    photo_file_id: UUID | None
    entries_count: int
    entries_by_kind: dict[str, int]
    updated_at: datetime


class AdminUserDetail(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None
    persona_kind: str
    is_active: bool
    is_superuser: bool
    email_verified_at: datetime | None
    last_login_at: datetime | None
    created_at: datetime
    student: AdminStudentSummary | None


# ---- Activity -----------------------------------------------------------


class AdminActivityRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    user_email: str | None
    kind: str
    status: Literal["ok", "error"]
    duration_ms: int | None
    error_message: str | None
    meta: dict[str, Any]
    created_at: datetime


class AdminActivityResponse(BaseModel):
    items: list[AdminActivityRow]
    total: int
    page: int
    size: int


# ---- Read-only entry inspection (for LLM audit) -------------------------


class AdminEntryDetail(BaseModel):
    """One student's StudentProfileEntry, read-only, exposed to admins
    so they can audit LLM-generated content (e.g. `details.ai_bullets`
    for internships) without impersonating the student.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kind: str
    title: str
    organization: str | None
    start_date: date | None
    end_date: date | None
    is_current: bool
    description: str | None
    url: str | None
    details: dict[str, Any]
    sort_order: int
    created_at: datetime
    updated_at: datetime


class AdminEntriesResponse(BaseModel):
    items: list[AdminEntryDetail]


# ---- Actions ------------------------------------------------------------


class AdminActionResult(BaseModel):
    ok: bool = True
    message: str | None = None


class AdminImpersonateResponse(BaseModel):
    """Superuser gets a fresh (access, refresh) pair for the target user.

    The frontend swaps its own tokens in the auth store; a header hint
    is added so the frontend can render an "impersonating" banner.
    """

    target_user_id: UUID
    target_user_email: EmailStr
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AdminUserDeleteRequest(BaseModel):
    """Confirm-with-typed-email pattern. Superuser must supply the target
    user's exact email in the body — protects against fat-fingered clicks.
    """

    confirm_email: EmailStr = Field(
        description="Must exactly match the target user's email"
    )


# ---- CV templates -------------------------------------------------------


class AdminCvTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    display_name: str
    description: str
    is_visible: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class AdminCvTemplateListResponse(BaseModel):
    items: list[AdminCvTemplateRead]


class AdminCvTemplateUpdate(BaseModel):
    """PATCH body — only fields the admin actually changed are sent."""

    is_visible: bool | None = None
    sort_order: int | None = Field(default=None, ge=0, le=10_000)


# ---- Daily report -------------------------------------------------------


class DailyReportRequest(BaseModel):
    """Optional payload for on-demand backfills. When Cloud Scheduler
    fires the default cron, `window_hours` is omitted and 24 is used.
    """

    window_hours: int = Field(default=24, ge=1, le=24 * 30)


class DailyReportResult(BaseModel):
    recipients: int
    delivered: int
    errors: list[str] = Field(default_factory=list)


# ---- Admin-triggered emails ---------------------------------------------


class EmailPreviewResponse(BaseModel):
    """What the admin sees before hitting Send.

    `recent_send_at` is the most recent timestamp this template was sent
    to this user within the last 7 days (from the usage_events audit
    trail); null means no recent send.
    """

    subject: str
    html: str
    text: str
    recipient_email: EmailStr
    recipient_name: str | None = None
    recent_send_at: datetime | None = None


class SendEmailRequest(BaseModel):
    template_id: str = Field(min_length=1, max_length=64)


class SendEmailBulkRequest(BaseModel):
    user_ids: list[UUID] = Field(min_length=1, max_length=200)
    template_id: str = Field(min_length=1, max_length=64)
    # `dry_run=true` returns per-recipient info without sending. `dry_run=false`
    # actually sends. The frontend calls dry_run first, shows the recipient
    # list with recent-send warnings, then submits again with dry_run=false.
    dry_run: bool = False


class BulkRecipient(BaseModel):
    user_id: UUID
    email: EmailStr
    full_name: str | None = None
    has_recent_send: bool = False


class SendEmailBulkDryRunResponse(BaseModel):
    template_id: str
    recipients: list[BulkRecipient]


class BulkFailure(BaseModel):
    user_id: UUID
    error: str


class SendEmailBulkResponse(BaseModel):
    template_id: str
    sent: int
    skipped: int  # e.g. user has no email or is disabled
    failed: list[BulkFailure] = Field(default_factory=list)
