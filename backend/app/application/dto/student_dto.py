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
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

STUDENT_ENTRY_KINDS = Literal[
    "course",
    "project",
    "internship",
    "volunteer",
    "certificate",
    "skill",
    "award",
    "extracurricular",
    "language",
]


# ---- profile -----------------------------------------------------------


def _normalize_profile_url(value: str | None, *, host_contains: str) -> str | None:
    """Accept blank/None as 'unset'; otherwise require http(s) + host match + a path.

    Kept lenient: LinkedIn slugs, GitHub sub-paths, trailing '/foo' etc. all
    pass. Only rejects obvious junk ('not a url'), wrong domains, and non-http
    schemes — enough to block silly client bugs without whack-a-mole regexes.
    """
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    parsed = urlparse(stripped)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("URL must start with http:// or https://")
    host = (parsed.netloc or "").lower()
    if host_contains not in host:
        raise ValueError(f"URL must be on {host_contains}")
    if not parsed.path.strip("/"):
        raise ValueError("URL must include a profile path")
    return stripped


class StudentLinks(BaseModel):
    github: str | None = None
    linkedin: str | None = None
    website: str | None = None
    portfolio: str | None = None

    @field_validator("linkedin", mode="before")
    @classmethod
    def _validate_linkedin(cls, v: str | None) -> str | None:
        return _normalize_profile_url(v, host_contains="linkedin.com")

    @field_validator("github", mode="before")
    @classmethod
    def _validate_github(cls, v: str | None) -> str | None:
        return _normalize_profile_url(v, host_contains="github.com")


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

    # Photo crop transform (see model docstring). Frontend clamps at
    # the same bounds; server enforces here so a malicious client
    # can't scribble outside them.
    photo_offset_x: int | None = Field(default=None, ge=0, le=100)
    photo_offset_y: int | None = Field(default=None, ge=0, le=100)
    photo_zoom: int | None = Field(default=None, ge=100, le=300)

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
    photo_offset_x: int
    photo_offset_y: int
    photo_zoom: int
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

    field: Literal[
        "summary",
        "project_description",
        "volunteer_description",
        "internship_description",
    ]
    text: str = Field(min_length=1, max_length=4000)
    context: dict[str, Any] | None = None


class TextCoachResponse(BaseModel):
    ok: bool
    rewritten: str
    notes: list[str] = Field(default_factory=list)


INTERNSHIP_FIELDS = Literal[
    "software_engineering",
    "data_analysis",
    "marketing",
    "hr",
    "finance",
    "design",
    "customer_support",
    "other",
]


class InternshipCoachRequest(BaseModel):
    """Raw fields the student typed into the Internship card. The
    backend LLM converts these into a short summary + 2–4 ATS-friendly
    bullets. If the input is too thin to make useful bullets, the
    response returns `vague=true` with two follow-up questions instead
    of guessing.
    """

    organization: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=200)
    field_: INTERNSHIP_FIELDS | None = Field(default=None, alias="field")
    location: str | None = Field(default=None, max_length=200)
    work_mode: Literal["on_site", "remote", "hybrid"] | None = None
    department: str | None = Field(default=None, max_length=200)
    responsibilities: str | None = Field(default=None, max_length=4000)
    achievements: str | None = Field(default=None, max_length=4000)
    tools: list[str] = Field(default_factory=list)
    skills_gained: list[str] = Field(default_factory=list)
    # If the previous coach call returned vague=true, the student's
    # answers get folded back in here so the LLM has more to work with.
    follow_up_answers: list[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class InternshipCoachResponse(BaseModel):
    ok: bool
    vague: bool = False
    summary: str | None = None
    bullets: list[str] = Field(default_factory=list)
    # LLM's suggested tools + skills — the student can accept or ignore.
    tools_suggested: list[str] = Field(default_factory=list)
    skills_suggested: list[str] = Field(default_factory=list)
    follow_ups: list[str] = Field(default_factory=list)
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
