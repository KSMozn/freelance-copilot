from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.infrastructure.db.models.job_analysis import JobAnalysis as AnalysisModel
from app.infrastructure.db.models.opportunity_score import OpportunityScore as ScoreModel


def _analysis_to_domain(row: AnalysisModel) -> DomainAnalysis:
    raw_risks = row.risks or []
    risks = [
        RiskItem(
            risk=str(r.get("risk", "")),
            severity=str(r.get("severity", "medium")),
            mitigation=str(r.get("mitigation", "")),
        )
        for r in raw_risks
        if isinstance(r, dict)
    ]
    raw_stack = row.stack_requirements or []
    stack = [
        StackRequirement(
            category=str(item.get("category", "tech_stack")),
            name=str(item.get("name", "")),
            importance=int(item.get("importance", 3)),
        )
        for item in raw_stack
        if isinstance(item, dict) and item.get("name")
    ]
    return DomainAnalysis(
        id=row.id,
        job_id=row.job_id,
        summary=row.summary,
        required_skills=list(row.required_skills or []),
        preferred_skills=list(row.preferred_skills or []),
        technologies=list(row.technologies or []),
        business_domain=row.business_domain,
        seniority=row.seniority,
        complexity=row.complexity,
        estimated_hours_min=row.estimated_hours_min,
        estimated_hours_max=row.estimated_hours_max,
        budget_assessment=row.budget_assessment,
        client_intent=row.client_intent,
        hidden_requirements=list(row.hidden_requirements or []),
        expected_deliverables=list(row.expected_deliverables or []),
        risks=risks,
        red_flags=list(row.red_flags or []),
        green_flags=list(row.green_flags or []),
        questions_to_ask_client=list(row.questions_to_ask_client or []),
        risk_level=row.risk_level,
        communication_required=row.communication_required,
        provider=row.provider,
        model=row.model,
        prompt_version=row.prompt_version,
        stack_requirements=stack,
        raw_response=row.raw_response,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _score_to_domain(row: ScoreModel) -> DomainScore:
    return DomainScore(
        id=row.id,
        job_id=row.job_id,
        analysis_id=row.analysis_id,
        score=row.score,
        recommendation=row.recommendation,
        confidence=row.confidence,
        score_breakdown=dict(row.score_breakdown or {}),
        reasoning=row.reasoning,
        profile_version=row.profile_version,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SQLAlchemyJobAnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_job_id(self, job_id: UUID) -> DomainAnalysis | None:
        stmt = select(AnalysisModel).where(AnalysisModel.job_id == job_id)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _analysis_to_domain(row) if row else None

    async def list_for_user(self, user_id: UUID) -> list[DomainAnalysis]:
        from app.infrastructure.db.models.job import Job

        stmt = (
            select(AnalysisModel)
            .join(Job, Job.id == AnalysisModel.job_id)
            .where(Job.user_id == user_id)
            .order_by(AnalysisModel.created_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_analysis_to_domain(r) for r in rows]

    async def upsert(
        self,
        *,
        job_id: UUID,
        summary: str | None,
        required_skills: list[str],
        preferred_skills: list[str],
        technologies: list[str],
        business_domain: str | None,
        seniority: str | None,
        complexity: str | None,
        estimated_hours_min: int | None,
        estimated_hours_max: int | None,
        budget_assessment: str | None,
        client_intent: str | None,
        hidden_requirements: list[str],
        expected_deliverables: list[str],
        risks: list[RiskItem],
        red_flags: list[str],
        green_flags: list[str],
        questions_to_ask_client: list[str],
        risk_level: str | None,
        communication_required: str | None,
        provider: str,
        model: str,
        prompt_version: str,
        stack_requirements: list[StackRequirement],
        raw_response: dict[str, Any] | None,
    ) -> DomainAnalysis:
        stmt = select(AnalysisModel).where(AnalysisModel.job_id == job_id)
        existing = (await self._session.execute(stmt)).scalar_one_or_none()

        serialized_risks = [
            {"risk": r.risk, "severity": r.severity, "mitigation": r.mitigation} for r in risks
        ]
        serialized_stack = [
            {"category": s.category, "name": s.name, "importance": s.importance}
            for s in stack_requirements
        ]

        if existing is None:
            row = AnalysisModel(
                job_id=job_id,
                summary=summary,
                required_skills=required_skills,
                preferred_skills=preferred_skills,
                technologies=technologies,
                business_domain=business_domain,
                seniority=seniority,
                complexity=complexity,
                estimated_hours_min=estimated_hours_min,
                estimated_hours_max=estimated_hours_max,
                budget_assessment=budget_assessment,
                client_intent=client_intent,
                hidden_requirements=hidden_requirements,
                expected_deliverables=expected_deliverables,
                risks=serialized_risks,
                red_flags=red_flags,
                green_flags=green_flags,
                questions_to_ask_client=questions_to_ask_client,
                stack_requirements=serialized_stack,
                risk_level=risk_level,
                communication_required=communication_required,
                provider=provider,
                model=model,
                prompt_version=prompt_version,
                raw_response=raw_response,
            )
            self._session.add(row)
        else:
            existing.summary = summary
            existing.required_skills = required_skills
            existing.preferred_skills = preferred_skills
            existing.technologies = technologies
            existing.business_domain = business_domain
            existing.seniority = seniority
            existing.complexity = complexity
            existing.estimated_hours_min = estimated_hours_min
            existing.estimated_hours_max = estimated_hours_max
            existing.budget_assessment = budget_assessment
            existing.client_intent = client_intent
            existing.hidden_requirements = hidden_requirements
            existing.expected_deliverables = expected_deliverables
            existing.risks = serialized_risks
            existing.red_flags = red_flags
            existing.green_flags = green_flags
            existing.questions_to_ask_client = questions_to_ask_client
            existing.stack_requirements = serialized_stack
            existing.risk_level = risk_level
            existing.communication_required = communication_required
            existing.provider = provider
            existing.model = model
            existing.prompt_version = prompt_version
            existing.raw_response = raw_response
            row = existing

        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _analysis_to_domain(row)


class SQLAlchemyOpportunityScoreRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_job_id(self, job_id: UUID) -> DomainScore | None:
        stmt = select(ScoreModel).where(ScoreModel.job_id == job_id)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _score_to_domain(row) if row else None

    async def upsert(
        self,
        *,
        job_id: UUID,
        analysis_id: UUID,
        score: int,
        recommendation: str,
        confidence: str,
        score_breakdown: dict[str, int],
        reasoning: str,
        profile_version: str,
    ) -> DomainScore:
        stmt = select(ScoreModel).where(ScoreModel.job_id == job_id)
        existing = (await self._session.execute(stmt)).scalar_one_or_none()

        if existing is None:
            row = ScoreModel(
                job_id=job_id,
                analysis_id=analysis_id,
                score=score,
                recommendation=recommendation,
                confidence=confidence,
                score_breakdown=score_breakdown,
                reasoning=reasoning,
                profile_version=profile_version,
            )
            self._session.add(row)
        else:
            existing.analysis_id = analysis_id
            existing.score = score
            existing.recommendation = recommendation
            existing.confidence = confidence
            existing.score_breakdown = score_breakdown
            existing.reasoning = reasoning
            existing.profile_version = profile_version
            row = existing

        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _score_to_domain(row)
