from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class StarStorySchema(BaseModel):
    """Interview-ready STAR story for a repository."""

    model_config = ConfigDict(extra="ignore")

    headline: str = Field(min_length=1, max_length=160)
    situation: str = Field(min_length=1, max_length=400)
    task: str = Field(min_length=1, max_length=400)
    action: str = Field(min_length=1, max_length=600)
    result: str = Field(min_length=1, max_length=400)


class RepositoryCreate(BaseModel):
    github_url: HttpUrl
    scan_now: bool = True


class RepositoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    github_url: str
    owner: str
    name: str
    default_branch: str | None
    description: str | None
    languages: dict[str, int]
    frameworks: list[str]
    libraries: list[str]
    databases: list[str]
    authentication: list[str]
    ai_providers: list[str]
    cloud: list[str]
    ci_systems: list[str]
    test_frameworks: list[str]
    has_docker: bool
    has_ci: bool
    has_tests: bool
    architecture_summary: str | None
    business_domain: str | None
    strengths: list[str]
    highlights: list[str]
    readme_excerpt: str | None
    scan_status: str
    scan_error: str | None
    scanned_at: datetime | None = None
    star_story: StarStorySchema | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RepositoryListResponse(BaseModel):
    items: list[RepositoryRead]
    total: int
    limit: int
    offset: int


class RepositoryMatch(BaseModel):
    """One repository's match against a job — mirrors PortfolioMatch shape so
    the frontend can render them with the same card component.
    """

    repository_id: UUID
    owner: str
    name: str
    github_url: str
    match_score: float = Field(ge=0.0, le=1.0)
    semantic_score: float = Field(ge=0.0, le=1.0)
    skill_overlap_score: float = Field(ge=0.0, le=1.0)
    domain_overlap_score: float = Field(ge=0.0, le=1.0)
    architecture_score: float = Field(ge=0.0, le=1.0)
    match_reasons: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    relevant_domains: list[str]
    relevant_paths: list[str]
    suggested_talking_points: list[str]


class RepositoryMatchesResponse(BaseModel):
    job_id: UUID
    matches: list[RepositoryMatch]
    embedding_provider: str
    embedding_model: str
    repository_count: int
