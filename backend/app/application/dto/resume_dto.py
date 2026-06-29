from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

Seniority = Literal["junior", "mid", "senior", "lead", "staff", "principal"]


class ResumeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    target_role: str | None = Field(default=None, max_length=160)
    summary: str | None = None
    seniority_level: Seniority | None = None
    primary_skills: list[str] = Field(default_factory=list)
    secondary_skills: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    project_highlights: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    notes: str | None = None


class ResumeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    target_role: str | None = Field(default=None, max_length=160)
    summary: str | None = None
    seniority_level: Seniority | None = None
    primary_skills: list[str] | None = None
    secondary_skills: list[str] | None = None
    industries: list[str] | None = None
    domains: list[str] | None = None
    achievements: list[str] | None = None
    project_highlights: list[str] | None = None
    keywords: list[str] | None = None
    notes: str | None = None


class ResumeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    target_role: str | None
    summary: str | None
    seniority_level: str | None
    primary_skills: list[str]
    secondary_skills: list[str]
    industries: list[str]
    domains: list[str]
    achievements: list[str]
    project_highlights: list[str]
    keywords: list[str]
    notes: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ResumeListResponse(BaseModel):
    items: list[ResumeRead]
    total: int
    limit: int
    offset: int


class ResumeRecommendation(BaseModel):
    """One resume's fit for a job, decorated with explanation fields."""

    resume_id: UUID
    title: str
    match_score: float = Field(ge=0.0, le=1.0)
    semantic_score: float = Field(ge=0.0, le=1.0)
    skill_overlap_score: float = Field(ge=0.0, le=1.0)
    domain_overlap_score: float = Field(ge=0.0, le=1.0)
    seniority_alignment_score: float = Field(ge=0.0, le=1.0)
    fit_reasons: list[str]
    relevant_skills: list[str]
    missing_or_weak_skills: list[str]
    suggested_positioning: list[str]


class ResumeRecommendationsResponse(BaseModel):
    job_id: UUID
    recommendations: list[ResumeRecommendation]
    embedding_provider: str
    embedding_model: str
    resume_count: int
