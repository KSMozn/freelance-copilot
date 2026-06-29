from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RepositoryImprovement(BaseModel):
    """One missing-skill suggestion for a specific repository."""

    model_config = ConfigDict(extra="ignore")

    skill: str
    suggestion: str  # short imperative — "Implement Stripe Billing."
    job_frequency: int  # number of user's analyzed jobs requesting this skill
    job_frequency_pct: float = Field(ge=0.0, le=1.0)


class RepositoryImprovements(BaseModel):
    """Improvement list for a single repository."""

    repository_id: UUID
    owner: str
    name: str
    github_url: str
    improvements: list[RepositoryImprovement] = Field(default_factory=list)


class RepositoryImprovementsReport(BaseModel):
    """All improvements across the user's scanned repositories."""

    repositories: list[RepositoryImprovements]
    analyzed_job_count: int  # denominator for `job_frequency_pct`
    repository_count: int
