"""DTOs for the Student persona surfaces.

Three families live here:
  * Profile read / update — the wizard's per-step PATCH-like payload, plus
    the full read shape rendered by the preview page.
  * Entries CRUD — courses / projects / volunteer / certificates / skills /
    languages / awards / extracurriculars all share one DTO with a `kind`
    discriminator and a kind-specific `details` blob.
  * Coaching responses — `ok` plus a small list of `warnings` and
    `suggestions` the wizard surfaces inline.

All fields except a handful of identifiers are optional because the wizard
saves progressively: step 1 only knows full_name + email, step 4 adds
summary, etc. Persist whatever's there.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

STUDENT_ENTRY_KINDS = Literal[
    "course",
    "project",
    "volunteer",
    "certificate",
    "skill",
    "award",
    "extracurricular",
    "language",
]


# ---- profile -----------------------------------------------------------


class StudentLinks(BaseModel):
    github: str | None = None
    linkedin: str | None = None
    website: str | None = None
    portfolio: str | None = None


class StudentProfileUpdate(BaseModel):
    """Per-step payload. Every field is optional — the wizard sends only
    what the step touched. `mark_steps` lists step slugs to append to
    `completed_steps` on save; `current_step` records where to land the
    user on return.
    """

    full_name: str | None = Field(default=None, max_length=255)
    professional_email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=64)
    location: str | None = Field(default=None, max_length=255)
    # ISO YYYY-MM-DD. Frontend composes from Day/Month/Year dropdowns.
    date_of_birth: date | None = None

    college: str | None = Field(default=None, max_length=255)
    department: str | None = Field(default=None, max_length=200)
    degree: str | None = Field(default=None, max_length=120)
    major: str | None = Field(default=None, max_length=255)
    graduation_year: int | None = Field(default=None, ge=1950, le=2099)
    gpa: Decimal | None = Field(default=None, ge=0, le=4.5, decimal_places=2)

    summary: str | None = None
    headline: str | None = Field(default=None, max_length=255)
    links: StudentLinks | None = None
    interests: list[str] | None = None

    # Selected CV template slug. Frontend writes this when the student
    # clicks "Set as default" in the Preview step. Validated at render
    # time via CvTemplateService, not here — an unknown slug just falls
    # back to the default instead of blocking save.
    cv_template_slug: str | None = Field(default=None, max_length=64)

    mark_steps: list[str] | None = None
    current_step: str | None = Field(default=None, max_length=64)


class StudentProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
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
    gpa: Decimal | None
    photo_file_id: UUID | None
    photo_url: str | None = None
    summary: str | None
    headline: str | None
    links: dict[str, Any]
    interests: list[Any]
    completed_steps: list[str]
    current_step: str | None
    cv_template_slug: str | None = None
    created_at: datetime
    updated_at: datetime


class CvTemplateRead(BaseModel):
    """Student-facing view of a CV template (picker card).

    Only visible templates are ever exposed through this DTO; the admin
    equivalent lives on `AdminCvTemplateRead` in `admin_dto`.
    """

    model_config = ConfigDict(from_attributes=True)

    slug: str
    display_name: str
    description: str
    sort_order: int


class CvTemplateListResponse(BaseModel):
    items: list[CvTemplateRead]
    default_slug: str  # what the renderer will use if no override is passed


# ---- entries -----------------------------------------------------------


class StudentEntryUpsert(BaseModel):
    kind: STUDENT_ENTRY_KINDS
    title: str = Field(min_length=1, max_length=255)
    organization: str | None = Field(default=None, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    description: str | None = None
    url: str | None = Field(default=None, max_length=512)
    details: dict[str, Any] = Field(default_factory=dict)
    sort_order: int = 0


class StudentEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kind: STUDENT_ENTRY_KINDS
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


class StudentEntryListResponse(BaseModel):
    items: list[StudentEntryRead]


# ---- coaching ----------------------------------------------------------


class CoachWarning(BaseModel):
    code: str
    message: str
    severity: Literal["info", "warn", "block"] = "warn"


class CoachSuggestion(BaseModel):
    label: str
    value: str
    rationale: str | None = None


class EmailCoachRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    full_name: str | None = Field(default=None, max_length=255)


class EmailCoachResponse(BaseModel):
    ok: bool
    warnings: list[CoachWarning] = Field(default_factory=list)
    suggestions: list[CoachSuggestion] = Field(default_factory=list)


class PhotoCoachResponse(BaseModel):
    ok: bool
    warnings: list[CoachWarning] = Field(default_factory=list)
    summary: str | None = None


class TextCoachRequest(BaseModel):
    """LLM-rewrites a piece of student text (a project blurb, summary,
    volunteer description). The wizard previews the suggestion and lets
    the student accept or keep their original.
    """

    field: Literal["summary", "project_description", "volunteer_description"]
    text: str = Field(min_length=1, max_length=4000)
    context: dict[str, Any] | None = None


class TextCoachResponse(BaseModel):
    ok: bool
    rewritten: str
    notes: list[str] = Field(default_factory=list)


class DraftSummaryResponse(BaseModel):
    """Auto-generated CV headline + summary, drafted from the student's
    profile + entries. The wizard surfaces it as a *suggestion* — the
    student can use it as-is, edit it, or regenerate.
    """

    ok: bool
    headline: str
    summary: str
    notes: list[str] = Field(default_factory=list)


class ProofreadFix(BaseModel):
    """One targeted proofreading suggestion (typo / grammar / clarity /
    style). The student sees the diff and clicks Apply or Ignore per fix.
    """

    entity_kind: Literal["profile", "entry"]
    entity_id: str | None = None  # entry UUID when entity_kind == "entry"
    field: Literal["summary", "headline", "description", "title"]
    original: str
    suggested: str
    reason: str
    category: Literal["typo", "grammar", "clarity", "style"]


class ProofreadResponse(BaseModel):
    ok: bool
    fixes: list[ProofreadFix] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


# ---- CV preview --------------------------------------------------------


class CvPreviewResponse(BaseModel):
    html: str
