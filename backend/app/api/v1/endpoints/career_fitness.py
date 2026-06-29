from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.dto.career_fitness_dto import (
    CareerFitnessRead,
    FeedbackRead,
    MarketSkillRead,
    RecurringGapRead,
    RepoSuggestionRead,
    SkillGapRead,
)
from app.application.services.career_fitness_service import (
    CareerFitness,
    CareerFitnessService,
)
from app.core.deps import CurrentUser, get_career_fitness_assembler

router = APIRouter(prefix="/career-fitness", tags=["career-fitness"])


@router.get("", response_model=CareerFitnessRead)
async def get_career_fitness(
    user: CurrentUser,
    assemble: Annotated[
        callable, Depends(get_career_fitness_assembler)
    ],
) -> CareerFitnessRead:
    """Aggregated market signals + gaps + repo nudges for the current user.

    Computed on demand from the user's job analyses, applications, match
    reports, repositories, and skill pot. No new tables — the dashboard
    stays as fresh as the underlying rows.
    """
    payload: CareerFitness = await assemble(user.id)
    return _to_read(payload)


def _to_read(c: CareerFitness) -> CareerFitnessRead:
    return CareerFitnessRead(
        total_jobs_analyzed=c.total_jobs_analyzed,
        total_applications=c.total_applications,
        market_skills=[
            MarketSkillRead(
                name=m.name,
                market_count=m.market_count,
                raw_required=m.raw_required,
                raw_preferred=m.raw_preferred,
                in_your_pot=m.in_your_pot,
                your_proficiency=m.your_proficiency,
                your_evidence_count=m.your_evidence_count,
            )
            for m in c.market_skills
        ],
        top_gaps=[
            SkillGapRead(
                name=g.name,
                market_count=g.market_count,
                current_proficiency=g.current_proficiency,
                severity=g.severity,
            )
            for g in c.top_gaps
        ],
        feedback=[FeedbackRead(name=f.name, score=f.score) for f in c.feedback],
        recurring_gaps=[
            RecurringGapRead(name=r.name, count=r.count, avg_importance=r.avg_importance)
            for r in c.recurring_gaps
        ],
        repo_suggestions=[
            RepoSuggestionRead(
                repository_id=r.repository_id,
                repository_name=r.repository_name,
                suggestion=r.suggestion,
                skills_covered=r.skills_covered,
            )
            for r in c.repo_suggestions
        ],
        domain_demand=c.domain_demand,
    )
