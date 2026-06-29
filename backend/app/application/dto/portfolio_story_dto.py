from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PortfolioStoryRead(BaseModel):
    """A tailored lead-with-this story picked for a specific job.

    `opener` is the 1-sentence hook the proposal can quote verbatim. `body`
    is a 2–3 sentence narrative grounded in the chosen portfolio. `why_this_fit`
    explains the pick — useful when multiple portfolios are close.
    """

    model_config = ConfigDict(extra="ignore")

    job_id: UUID
    portfolio_id: UUID
    portfolio_title: str
    business_domain: str | None = None
    match_score: float = Field(ge=0.0, le=1.0)
    opener: str = Field(min_length=1, max_length=400)
    body: str = Field(min_length=1, max_length=800)
    why_this_fit: str = Field(min_length=1, max_length=400)
    relevant_skills: list[str] = Field(default_factory=list)
