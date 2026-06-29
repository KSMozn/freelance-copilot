from pydantic import BaseModel, ConfigDict, Field


class MarketSkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    market_count: float = Field(ge=0)
    raw_required: int = Field(ge=0)
    raw_preferred: int = Field(ge=0)
    in_your_pot: bool
    your_proficiency: int | None = Field(default=None, ge=1, le=5)
    your_evidence_count: int = Field(ge=0)


class SkillGapRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    market_count: float = Field(ge=0)
    current_proficiency: int | None = Field(default=None, ge=1, le=5)
    severity: int = Field(ge=1, le=5)


class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    score: int


class RecurringGapRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    count: int = Field(ge=0)
    avg_importance: float = Field(ge=0, le=5)


class RepoSuggestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    repository_id: str
    repository_name: str
    suggestion: str
    skills_covered: list[str] = Field(default_factory=list)


class CareerFitnessRead(BaseModel):
    total_jobs_analyzed: int
    total_applications: int
    market_skills: list[MarketSkillRead] = Field(default_factory=list)
    top_gaps: list[SkillGapRead] = Field(default_factory=list)
    feedback: list[FeedbackRead] = Field(default_factory=list)
    recurring_gaps: list[RecurringGapRead] = Field(default_factory=list)
    repo_suggestions: list[RepoSuggestionRead] = Field(default_factory=list)
    domain_demand: list[tuple[str, int]] = Field(default_factory=list)
