"""Pick the best portfolio for a job and write a tailored lead-with story.

Picking is deterministic (top match from PortfolioMatchingService). The
narrative is a single AI call so the prose actually references the job, not
just the portfolio. Schema-validated, no persistence — react-query caches
on the client side and the AI cost is small.
"""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.application.dto.portfolio_story_dto import PortfolioStoryRead
from app.application.services.portfolio_matching_service import (
    PortfolioMatchingService,
)
from app.domain.entities.job import Job
from app.domain.entities.portfolio import Portfolio
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.providers.ai_provider import AIProvider
from app.domain.repositories.analysis_repository import JobAnalysisRepository
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.portfolio_repository import PortfolioRepository
from app.infrastructure.ai.errors import AIProviderError

STORY_MARKER = "--- PORTFOLIO STORY ASSIGNMENT ---"

SYSTEM_PROMPT = """You are a senior engineering consultant writing the single \
strongest opener for an Upwork proposal — leading with the most relevant past \
project.

Hard rules:
- Reply with a single JSON object matching the schema in the user prompt. \
  Output nothing else — no prose, no markdown, no code fences.
- Ground every sentence in the supplied portfolio and job context. Never \
  invent technologies, outcomes, or projects.
- `opener` is ONE sentence the proposal can quote first — specific, no \
  greeting, no hype, no "excited to apply" language.
- `body` is 2–3 sentences continuing from the opener: what the portfolio is, \
  why it lines up with this job, one concrete outcome if available.
- `why_this_fit` is ONE sentence for internal explanation (UI tooltip) — \
  spells out the strongest connecting thread (skill / domain / architecture).
- Keep prose plain and senior. Avoid: "I am excited", "perfect fit", "extensive \
  experience", "thrilled", "love to work on".
"""


class _StoryPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    opener: str = Field(min_length=1, max_length=400)
    body: str = Field(min_length=1, max_length=800)
    why_this_fit: str = Field(min_length=1, max_length=400)


def _build_prompt(*, job: Job, analysis, portfolio: Portfolio, match) -> str:
    lines = [
        STORY_MARKER,
        f"Job title: {job.title}",
        f"Job domain: {analysis.business_domain or '(unknown)'}",
    ]
    if analysis.summary:
        lines.append(f"Job summary: {analysis.summary}")
    job_skills = analysis.required_skills + analysis.preferred_skills + analysis.technologies
    if job_skills:
        lines.append("Job required skills: " + ", ".join(job_skills))

    lines.append("")
    lines.append(f"Chosen portfolio: {portfolio.title}")
    if portfolio.business_domain:
        lines.append(f"Portfolio domain: {portfolio.business_domain}")
    if portfolio.short_description:
        lines.append(f"Short description: {portfolio.short_description}")
    if portfolio.long_description:
        lines.append("Long description:")
        lines.append(portfolio.long_description[:1500])
    if portfolio.technologies:
        lines.append("Portfolio technologies: " + ", ".join(portfolio.technologies))
    if portfolio.outcomes:
        lines.append("Outcomes:")
        lines.extend(f"  - {o}" for o in portfolio.outcomes[:5])
    if match.match_reasons:
        lines.append("Why it matched: " + " · ".join(match.match_reasons[:4]))
    if match.relevant_skills:
        lines.append("Overlapping skills: " + ", ".join(match.relevant_skills))

    lines.extend(
        [
            "",
            "Return JSON only with these keys:",
            "{",
            '  "opener": string,         // 1 sentence',
            '  "body": string,           // 2–3 sentences',
            '  "why_this_fit": string    // 1 sentence',
            "}",
        ]
    )
    return "\n".join(lines)


class PortfolioStoryFailedError(DomainError):
    """Raised when story generation can't produce a valid payload."""


class PortfolioStoryService:
    def __init__(
        self,
        *,
        job_repo: JobRepository,
        analysis_repo: JobAnalysisRepository,
        portfolio_repo: PortfolioRepository,
        portfolio_matching: PortfolioMatchingService,
        ai_provider: AIProvider,
    ) -> None:
        self._jobs = job_repo
        self._analyses = analysis_repo
        self._portfolios = portfolio_repo
        self._matching = portfolio_matching
        self._ai = ai_provider

    async def build(self, *, user_id: UUID, job_id: UUID) -> PortfolioStoryRead | None:
        job = await self._jobs.get_by_id(job_id, user_id=user_id)
        if job is None:
            raise NotFoundError("Job not found")
        analysis = await self._analyses.get_by_job_id(job_id)
        if analysis is None:
            raise NotFoundError("Job has not been analyzed yet — run /analyze first.")

        matches = await self._matching.match(user_id=user_id, job_id=job_id, top_n=3)
        if not matches.matches:
            return None
        top = matches.matches[0]

        portfolio = await self._portfolios.get_by_id(top.portfolio_id, user_id=user_id)
        if portfolio is None:
            # Match referenced a portfolio that's since been deleted — skip.
            return None

        try:
            raw = await self._ai.complete_json(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=_build_prompt(
                    job=job, analysis=analysis, portfolio=portfolio, match=top
                ),
            )
        except AIProviderError as exc:
            raise PortfolioStoryFailedError(f"AI provider error: {exc}") from exc

        try:
            payload = _StoryPayload.model_validate(raw.data)
        except ValidationError as exc:
            raise PortfolioStoryFailedError(
                f"AI response did not match the story schema: {exc.errors()[:3]}"
            ) from exc

        return PortfolioStoryRead(
            job_id=job.id,
            portfolio_id=portfolio.id,
            portfolio_title=portfolio.title,
            business_domain=portfolio.business_domain,
            match_score=top.match_score,
            opener=payload.opener,
            body=payload.body,
            why_this_fit=payload.why_this_fit,
            relevant_skills=list(top.relevant_skills),
        )
