from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class PortfolioCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    short_description: str | None = Field(default=None, max_length=500)
    long_description: str = Field(min_length=1)
    role: str | None = Field(default=None, max_length=120)
    business_domain: str | None = Field(default=None, max_length=120)
    github_url: HttpUrl | None = None
    live_url: HttpUrl | None = None
    technologies: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    outcomes: list[str] = Field(default_factory=list)
    highlight: bool = False


class PortfolioUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    short_description: str | None = Field(default=None, max_length=500)
    long_description: str | None = Field(default=None, min_length=1)
    role: str | None = Field(default=None, max_length=120)
    business_domain: str | None = Field(default=None, max_length=120)
    github_url: HttpUrl | None = None
    live_url: HttpUrl | None = None
    technologies: list[str] | None = None
    skills: list[str] | None = None
    features: list[str] | None = None
    outcomes: list[str] | None = None
    highlight: bool | None = None


class PortfolioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    short_description: str | None
    long_description: str
    role: str | None
    business_domain: str | None
    github_url: str | None
    live_url: str | None
    technologies: list[str]
    skills: list[str]
    features: list[str]
    outcomes: list[str]
    highlight: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PortfolioListResponse(BaseModel):
    items: list[PortfolioRead]
    total: int
    limit: int
    offset: int


class PortfolioMatch(BaseModel):
    """One portfolio's match against a job, decorated with explanation fields."""

    portfolio_id: UUID
    title: str
    match_score: float = Field(ge=0.0, le=1.0)
    semantic_score: float = Field(ge=0.0, le=1.0)
    skill_overlap_score: float = Field(ge=0.0, le=1.0)
    domain_overlap_score: float = Field(ge=0.0, le=1.0)
    strategic_score: float = Field(ge=0.0, le=1.0)
    match_reasons: list[str]
    relevant_skills: list[str]
    relevant_domains: list[str]
    suggested_talking_points: list[str]


class PortfolioMatchesResponse(BaseModel):
    job_id: UUID
    matches: list[PortfolioMatch]
    embedding_provider: str
    embedding_model: str
    portfolio_count: int  # total portfolios considered before slicing top-N
