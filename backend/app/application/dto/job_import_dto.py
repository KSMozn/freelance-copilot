from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

BudgetTypeLiteral = Literal["fixed", "hourly"]


class JobImportSchema(BaseModel):
    """Strict schema for what the multimodal AI must return when parsing an
    Upwork screenshot.

    Required: title + description. Everything else is optional — Upwork crops
    differently per user, so we let the model omit fields it can't see.
    Unknown extra keys are ignored so the contract stays forward-compatible.
    """

    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1)

    source_url: HttpUrl | None = None
    budget_type: BudgetTypeLiteral | None = None
    budget_min: Decimal | None = Field(default=None, ge=0)
    budget_max: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    proposal_count: int | None = Field(default=None, ge=0)

    # Rich-context fields used to build a usable description for the analyzer.
    # None of these are persisted as their own columns — we fold them into the
    # description so the existing Phase-2 analyzer can pick them up.
    project_duration: str | None = Field(default=None, max_length=120)
    project_type: str | None = Field(default=None, max_length=120)
    experience_level: str | None = Field(default=None, max_length=80)
    location: str | None = Field(default=None, max_length=120)
    posted_at: str | None = Field(default=None, max_length=80)
    mandatory_skills: list[str] = Field(default_factory=list, max_length=20)
    nice_to_have_skills: list[str] = Field(default_factory=list, max_length=20)
    questions: list[str] = Field(default_factory=list, max_length=10)


class JobImportPreview(BaseModel):
    """Returned as part of the response so the frontend can show what was
    extracted, before letting the user edit on the Job Detail page.
    """

    project_duration: str | None = None
    project_type: str | None = None
    experience_level: str | None = None
    location: str | None = None
    posted_at: str | None = None
    mandatory_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)


# The endpoint returns the persisted Job (using the existing JobRead) plus
# the structured extraction preview for the UI. JobRead lives in job_dto.py;
# this DTO composes them.
from app.application.dto.job_dto import JobRead


class JobImportResponse(BaseModel):
    job: JobRead
    preview: JobImportPreview
    provider: str
    model: str
