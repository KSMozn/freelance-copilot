"""Orchestrates analysis + scoring for a single job."""
from __future__ import annotations

from uuid import UUID

from pydantic import ValidationError

from app.application.dto.analysis_dto import (
    JobAnalysisRead,
    JobAnalysisResponse,
    JobAnalysisSchema,
    OpportunityScoreRead,
    RiskItemSchema,
    ScoreBreakdown,
    StackRequirementSchema,
)
from app.application.services.prompts import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    build_user_prompt,
)
from app.application.services.scoring_service import ScoringService
from app.domain.entities.analysis import (
    JobAnalysis as DomainAnalysis,
)
from app.domain.entities.analysis import (
    OpportunityScore as DomainScore,
)
from app.domain.entities.analysis import (
    RiskItem,
    StackRequirement,
)
from app.domain.entities.job import Job
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.providers.ai_provider import AIProvider
from app.domain.repositories.analysis_repository import (
    JobAnalysisRepository,
    OpportunityScoreRepository,
)
from app.domain.repositories.job_repository import JobRepository
from app.infrastructure.ai.errors import AIProviderError


class AnalysisFailedError(DomainError):
    """Raised when the AI provider produced an unusable response."""


def _format_budget(job: Job) -> str:
    if job.budget_min is None and job.budget_max is None:
        return "unspecified"
    if job.budget_type:
        prefix = f"{job.budget_type} "
    else:
        prefix = ""
    if job.budget_min == job.budget_max and job.budget_min is not None:
        return f"{prefix}{job.currency} {job.budget_min}"
    return f"{prefix}{job.currency} {job.budget_min or '?'}–{job.budget_max or '?'}"


class JobAnalysisService:
    def __init__(
        self,
        *,
        job_repo: JobRepository,
        analysis_repo: JobAnalysisRepository,
        score_repo: OpportunityScoreRepository,
        ai_provider: AIProvider,
        scoring: ScoringService,
    ) -> None:
        self._jobs = job_repo
        self._analyses = analysis_repo
        self._scores = score_repo
        self._ai = ai_provider
        self._scoring = scoring

    async def analyze(self, *, user_id: UUID, job_id: UUID) -> JobAnalysisResponse:
        job = await self._jobs.get_by_id(job_id, user_id=user_id)
        if job is None:
            raise NotFoundError("Job not found")

        user_prompt = build_user_prompt(
            title=job.title,
            description=job.description,
            budget=_format_budget(job),
            proposal_count=job.proposal_count if job.proposal_count is not None else "unknown",
        )

        try:
            raw = await self._ai.complete_json(
                system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt
            )
        except AIProviderError as exc:
            raise AnalysisFailedError(f"AI provider error: {exc}") from exc

        try:
            schema = JobAnalysisSchema.model_validate(raw.data)
        except ValidationError as exc:
            raise AnalysisFailedError(
                f"AI response did not match the analyzer schema: {exc.errors()[:3]}"
            ) from exc

        domain_analysis = await self._analyses.upsert(
            job_id=job.id,
            summary=schema.summary,
            required_skills=list(schema.required_skills),
            preferred_skills=list(schema.preferred_skills),
            technologies=list(schema.technologies),
            business_domain=schema.business_domain,
            seniority=schema.seniority_level,
            complexity=schema.complexity,
            estimated_hours_min=schema.estimated_hours_min,
            estimated_hours_max=schema.estimated_hours_max,
            budget_assessment=schema.budget_assessment,
            client_intent=schema.client_intent,
            hidden_requirements=list(schema.hidden_requirements),
            expected_deliverables=list(schema.deliverables),
            risks=[
                RiskItem(risk=r.risk, severity=r.severity, mitigation=r.mitigation)
                for r in schema.risks
            ],
            red_flags=list(schema.red_flags),
            green_flags=list(schema.green_flags),
            questions_to_ask_client=list(schema.questions_to_ask_client),
            risk_level=schema.risk_level,
            communication_required=schema.communication_required,
            provider=raw.provider,
            model=raw.model,
            prompt_version=PROMPT_VERSION,
            stack_requirements=[
                StackRequirement(category=s.category, name=s.name, importance=s.importance)
                for s in schema.stack_requirements
            ],
            raw_response=raw.data,
        )

        scoring_result = self._scoring.score(job=job, analysis=schema)
        domain_score = await self._scores.upsert(
            job_id=job.id,
            analysis_id=domain_analysis.id,
            score=scoring_result.score,
            recommendation=scoring_result.recommendation,
            confidence=scoring_result.confidence,
            score_breakdown=scoring_result.score_breakdown,
            reasoning=scoring_result.reasoning,
            profile_version=self._scoring.profile_version,
        )

        return _to_response(domain_analysis, domain_score)

    async def get(self, *, user_id: UUID, job_id: UUID) -> JobAnalysisResponse:
        job = await self._jobs.get_by_id(job_id, user_id=user_id)
        if job is None:
            raise NotFoundError("Job not found")
        analysis = await self._analyses.get_by_job_id(job_id)
        if analysis is None:
            raise NotFoundError("Job has not been analyzed yet")
        score = await self._scores.get_by_job_id(job_id)
        if score is None:
            raise NotFoundError("Job has analysis but no score yet")
        return _to_response(analysis, score)


def _to_response(
    analysis: DomainAnalysis, score: DomainScore
) -> JobAnalysisResponse:
    return JobAnalysisResponse(
        analysis=JobAnalysisRead(
            id=analysis.id,
            job_id=analysis.job_id,
            summary=analysis.summary,
            required_skills=analysis.required_skills,
            preferred_skills=analysis.preferred_skills,
            technologies=analysis.technologies,
            business_domain=analysis.business_domain,
            seniority=analysis.seniority,
            complexity=analysis.complexity,
            estimated_hours_min=analysis.estimated_hours_min,
            estimated_hours_max=analysis.estimated_hours_max,
            budget_assessment=analysis.budget_assessment,
            client_intent=analysis.client_intent,
            hidden_requirements=analysis.hidden_requirements,
            expected_deliverables=analysis.expected_deliverables,
            risks=[
                RiskItemSchema(risk=r.risk, severity=r.severity, mitigation=r.mitigation)  # type: ignore[arg-type]
                for r in analysis.risks
            ],
            red_flags=analysis.red_flags,
            green_flags=analysis.green_flags,
            questions_to_ask_client=analysis.questions_to_ask_client,
            risk_level=analysis.risk_level,
            communication_required=analysis.communication_required,
            provider=analysis.provider,
            model=analysis.model,
            prompt_version=analysis.prompt_version,
            stack_requirements=[
                StackRequirementSchema(category=s.category, name=s.name, importance=s.importance)  # type: ignore[arg-type]
                for s in analysis.stack_requirements
            ],
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
        ),
        score=OpportunityScoreRead(
            id=score.id,
            job_id=score.job_id,
            analysis_id=score.analysis_id,
            score=score.score,
            recommendation=score.recommendation,  # type: ignore[arg-type]
            confidence=score.confidence,  # type: ignore[arg-type]
            score_breakdown=ScoreBreakdown(**score.score_breakdown),
            reasoning=score.reasoning,
            profile_version=score.profile_version,
            created_at=score.created_at,
            updated_at=score.updated_at,
        ),
    )
