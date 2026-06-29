"""Orchestrates proposal generation + immediate quality review.

Pipeline:
    load job
  → require analysis + score (Phase 2)
  → fetch portfolio matches (Phase 3) — recomputes on the fly using the
    persisted job embedding + portfolio embeddings, so this is cheap
  → fetch resume recommendations (Phase 4) — same
  → build a compact prompt context
  → call AIProvider.complete_json
  → validate JSON against ProposalDraftSchema
  → review the draft (deterministic, Phase 5)
  → persist the proposal + its review

Returns the persisted proposal as a ProposalRead DTO.
"""
from __future__ import annotations

from uuid import UUID

from pydantic import ValidationError

from app.application.dto.proposal_dto import (
    ImplementationWeekSchema,
    ProposalDiagramSchema,
    ProposalDraftSchema,
    ProposalRead,
    ProposalStrategySchema,
)
from app.application.services.portfolio_matching_service import (
    DEFAULT_TOP_N as PORTFOLIO_DEFAULT_TOP_N,
    PortfolioMatchingService,
)
from app.application.services.proposal_context import (
    DEFAULT_TOP_PORTFOLIO,
    DEFAULT_TOP_RESUME,
    build_proposal_user_prompt,
)
from app.application.services.proposal_prompts import PROMPT_VERSION, SYSTEM_PROMPT
from app.application.services.proposal_review_service import ProposalReviewService
from app.application.services.resume_recommendation_service import (
    DEFAULT_TOP_N as RESUME_DEFAULT_TOP_N,
    ResumeRecommendationService,
)
from app.domain.entities.proposal import (
    ImplementationWeek,
    Milestone,
    Proposal,
    ProposalDiagram,
    ProposalStrategy,
)
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.providers.ai_provider import AIProvider
from app.domain.repositories.analysis_repository import (
    JobAnalysisRepository,
    OpportunityScoreRepository,
)
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.portfolio_repository import PortfolioRepository
from app.domain.repositories.proposal_repository import ProposalRepository
from app.infrastructure.ai.errors import AIProviderError


class ProposalGenerationFailedError(DomainError):
    """Raised when the provider response cannot be parsed into a valid proposal."""


def _strategy_to_schema(s: ProposalStrategy | None) -> ProposalStrategySchema | None:
    if s is None:
        return None
    return ProposalStrategySchema(
        angle=s.angle,  # type: ignore[arg-type]
        rationale=s.rationale,
        emphasis_points=list(s.emphasis_points),
    )


def _to_read(p: Proposal) -> ProposalRead:
    return ProposalRead(
        id=p.id,
        user_id=p.user_id,
        job_id=p.job_id,
        resume_id=p.resume_id,
        portfolio_ids=list(p.portfolio_ids),
        title=p.title,
        body=p.body,
        short_body=p.short_body,
        questions=list(p.questions),
        milestones=[
            {
                "name": m.name,
                "description": m.description,
                "estimated_hours": m.estimated_hours,
            }
            for m in p.milestones
        ],  # type: ignore[arg-type]
        delivery_approach=list(p.delivery_approach),
        risk_notes=list(p.risk_notes),
        quality_score=p.quality_score,
        quality_breakdown=p.quality_breakdown,
        quality_warnings=list(p.quality_warnings),
        strategy=_strategy_to_schema(p.strategy),
        implementation_plan=[
            ImplementationWeekSchema(
                week=w.week,
                focus=w.focus,
                summary=w.summary,
                deliverables=list(w.deliverables),
            )
            for w in p.implementation_plan
        ],
        diagrams=[
            ProposalDiagramSchema(kind=d.kind, title=d.title, mermaid=d.mermaid)  # type: ignore[arg-type]
            for d in p.diagrams
        ],
        prompt_version=p.prompt_version,
        model_provider=p.model_provider,
        model_name=p.model_name,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


class ProposalGenerationService:
    def __init__(
        self,
        *,
        job_repo: JobRepository,
        analysis_repo: JobAnalysisRepository,
        score_repo: OpportunityScoreRepository,
        portfolio_repo: PortfolioRepository,
        portfolio_matching_service: PortfolioMatchingService,
        resume_recommendation_service: ResumeRecommendationService,
        proposal_repo: ProposalRepository,
        ai_provider: AIProvider,
        review_service: ProposalReviewService,
    ) -> None:
        self._jobs = job_repo
        self._analyses = analysis_repo
        self._scores = score_repo
        self._portfolios = portfolio_repo
        self._matching = portfolio_matching_service
        self._resume_recs = resume_recommendation_service
        self._proposals = proposal_repo
        self._ai = ai_provider
        self._review = review_service

    async def generate(
        self,
        *,
        user_id: UUID,
        job_id: UUID,
        top_portfolio_n: int = DEFAULT_TOP_PORTFOLIO,
        top_resume_n: int = DEFAULT_TOP_RESUME,
    ) -> ProposalRead:
        job = await self._jobs.get_by_id(job_id, user_id=user_id)
        if job is None:
            raise NotFoundError("Job not found")
        analysis = await self._analyses.get_by_job_id(job_id)
        if analysis is None:
            raise NotFoundError(
                "Job has not been analyzed yet — run /analyze first."
            )
        score = await self._scores.get_by_job_id(job_id)
        if score is None:
            raise NotFoundError(
                "Job has analysis but no opportunity score — re-run /analyze."
            )

        portfolio_matches = await self._matching.match(
            user_id=user_id,
            job_id=job_id,
            top_n=max(PORTFOLIO_DEFAULT_TOP_N, top_portfolio_n),
        )
        resume_recs = await self._resume_recs.recommend(
            user_id=user_id,
            job_id=job_id,
            top_n=max(RESUME_DEFAULT_TOP_N, top_resume_n),
        )

        ctx = build_proposal_user_prompt(
            job=job,
            analysis=analysis,
            score=score,
            portfolio_matches=portfolio_matches,
            resume_recs=resume_recs,
            top_portfolio_n=top_portfolio_n,
            top_resume_n=top_resume_n,
        )

        try:
            raw = await self._ai.complete_json(
                system_prompt=SYSTEM_PROMPT, user_prompt=ctx.user_prompt
            )
        except AIProviderError as exc:
            raise ProposalGenerationFailedError(f"AI provider error: {exc}") from exc

        try:
            draft = ProposalDraftSchema.model_validate(raw.data)
        except ValidationError as exc:
            raise ProposalGenerationFailedError(
                f"AI response did not match the proposal schema: {exc.errors()[:3]}"
            ) from exc

        # Build the (un-persisted) Proposal entity so we can run the review on
        # it before saving — that way the persisted row already carries the
        # quality score and we never have a "scored = false" state.
        domain_milestones = [
            Milestone(
                name=m.name,
                description=m.description,
                estimated_hours=m.estimated_hours,
            )
            for m in draft.milestones
        ]
        portfolios_for_review = []
        if ctx.used_portfolio_ids:
            for pid in ctx.used_portfolio_ids:
                pf = await self._portfolios.get_by_id(pid, user_id=user_id)
                if pf is not None:
                    portfolios_for_review.append(pf)

        strategy = ProposalStrategy(
            angle=draft.strategy.angle,
            rationale=draft.strategy.rationale,
            emphasis_points=list(draft.strategy.emphasis_points),
        )
        implementation_plan = [
            ImplementationWeek(
                week=w.week,
                focus=w.focus,
                summary=w.summary,
                deliverables=list(w.deliverables),
            )
            for w in draft.implementation_plan
        ]
        diagrams = [
            ProposalDiagram(kind=d.kind, title=d.title, mermaid=d.mermaid)
            for d in draft.diagrams
        ]
        unsaved = Proposal(
            id=UUID(int=0),  # placeholder, replaced after persist
            user_id=user_id,
            job_id=job.id,
            resume_id=ctx.used_resume_id,
            portfolio_ids=list(ctx.used_portfolio_ids),
            title=draft.title,
            body=draft.body,
            short_body=draft.short_body,
            questions=list(draft.questions),
            milestones=domain_milestones,
            delivery_approach=list(draft.delivery_approach),
            risk_notes=list(draft.risk_notes),
            strategy=strategy,
            implementation_plan=implementation_plan,
            diagrams=diagrams,
        )
        review = self._review.review(
            proposal=unsaved, analysis=analysis, portfolios=portfolios_for_review
        )

        persisted = await self._proposals.create(
            user_id=user_id,
            job_id=job.id,
            resume_id=ctx.used_resume_id,
            portfolio_ids=list(ctx.used_portfolio_ids),
            title=draft.title,
            body=draft.body,
            short_body=draft.short_body,
            questions=list(draft.questions),
            milestones=domain_milestones,
            delivery_approach=list(draft.delivery_approach),
            risk_notes=list(draft.risk_notes),
            quality_score=review.quality_score,
            quality_breakdown=review.quality_breakdown.model_dump(),
            quality_warnings=review.warnings,
            strategy=strategy,
            implementation_plan=implementation_plan,
            diagrams=diagrams,
            prompt_version=PROMPT_VERSION,
            model_provider=raw.provider,
            model_name=raw.model,
            raw_response=raw.data,
        )
        return _to_read(persisted)

    async def get(self, *, user_id: UUID, proposal_id: UUID) -> ProposalRead:
        proposal = await self._proposals.get_by_id(proposal_id, user_id=user_id)
        if proposal is None:
            raise NotFoundError("Proposal not found")
        return _to_read(proposal)

    async def list_for_job(self, *, user_id: UUID, job_id: UUID) -> list[ProposalRead]:
        proposals = await self._proposals.list_by_job_id(job_id, user_id=user_id)
        return [_to_read(p) for p in proposals]

    async def get_latest_for_job(
        self, *, user_id: UUID, job_id: UUID
    ) -> ProposalRead | None:
        proposal = await self._proposals.get_latest_by_job_id(job_id, user_id=user_id)
        return _to_read(proposal) if proposal else None

    async def update(
        self,
        *,
        user_id: UUID,
        proposal_id: UUID,
        fields: dict[str, object],
    ) -> ProposalRead:
        existing = await self._proposals.get_by_id(proposal_id, user_id=user_id)
        if existing is None:
            raise NotFoundError("Proposal not found")

        normalized = dict(fields)
        if "milestones" in normalized and normalized["milestones"] is not None:
            normalized["milestones"] = [
                Milestone(
                    name=m["name"],
                    description=m["description"],
                    estimated_hours=m.get("estimated_hours"),
                )
                for m in normalized["milestones"]  # type: ignore[union-attr]
            ]

        updated = await self._proposals.update(
            proposal_id, user_id=user_id, fields=normalized
        )
        if updated is None:
            raise NotFoundError("Proposal not found")
        return _to_read(updated)

    async def delete(self, *, user_id: UUID, proposal_id: UUID) -> None:
        ok = await self._proposals.delete(proposal_id, user_id=user_id)
        if not ok:
            raise NotFoundError("Proposal not found")

    async def re_review(
        self, *, user_id: UUID, proposal_id: UUID
    ) -> ProposalRead:
        existing = await self._proposals.get_by_id(proposal_id, user_id=user_id)
        if existing is None:
            raise NotFoundError("Proposal not found")
        analysis = await self._analyses.get_by_job_id(existing.job_id)
        portfolios_for_review = []
        for pid in existing.portfolio_ids:
            pf = await self._portfolios.get_by_id(pid, user_id=user_id)
            if pf is not None:
                portfolios_for_review.append(pf)
        review = self._review.review(
            proposal=existing, analysis=analysis, portfolios=portfolios_for_review
        )
        updated = await self._proposals.update(
            proposal_id,
            user_id=user_id,
            fields={
                "quality_score": review.quality_score,
                "quality_breakdown": review.quality_breakdown.model_dump(),
                "quality_warnings": review.warnings,
            },
        )
        assert updated is not None  # we just read it; refresh path is in repo
        return _to_read(updated)
