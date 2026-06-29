"""MatchReportService — persona-aware match orchestrator.

Combines:
  * `JobConfidenceService.build` for the existing dimensions
    (technical / architecture / domain / interview_chance / rationale)
  * `leadership_signals` for the Phase E dimensions
    (leadership_fit / soft_skills_fit) — *abstains* (None) when the job
    doesn't carry those signals.
  * `GapRecommendationService` for actionable fixes per missing skill.

Persists the result via :class:`MatchReportRepository.upsert` keyed by
``(job_id, persona_id)``. Re-runs are cheap because callers can ask for
the cached row (``compute=False``) and only pay the LLM cost when they
hit "Re-run analysis."
"""
from __future__ import annotations

from uuid import UUID, uuid4

from app.application.services.gap_recommendation_service import (
    GapRecommendationService,
)
from app.application.services.job_confidence_service import JobConfidenceService
from app.application.services.leadership_signals import (
    detect_leadership_demand,
    detect_soft_demand,
    score_category_fit,
)
from app.application.services.persona_profile_resolver import PersonaProfileResolver
from app.application.services.skill_evidence_service import SkillEvidenceService
from app.domain.entities.match_report import MatchReport
from app.domain.exceptions import NotFoundError
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.match_report_repository import MatchReportRepository
from app.domain.repositories.persona_repository import PersonaRepository
from app.domain.repositories.skill_catalog_repository import SkillCatalogRepository
from app.domain.repositories.user_skill_repository import UserSkillRepository


class MatchReportService:
    def __init__(
        self,
        *,
        confidence: JobConfidenceService,
        evidence: SkillEvidenceService,
        gap_recs: GapRecommendationService,
        resolver: PersonaProfileResolver,
        jobs: JobRepository,
        personas: PersonaRepository,
        user_skills: UserSkillRepository,
        skill_catalog: SkillCatalogRepository,
        reports: MatchReportRepository,
    ) -> None:
        self._confidence = confidence
        self._evidence = evidence
        self._recs = gap_recs
        self._resolver = resolver
        self._jobs = jobs
        self._personas = personas
        self._user_skills = user_skills
        self._catalog = skill_catalog
        self._reports = reports

    async def build_or_get(
        self,
        *,
        user_id: UUID,
        job_id: UUID,
        persona_id: UUID | None = None,
        force: bool = False,
    ) -> MatchReport:
        """Return the persona-keyed report, computing it if absent or stale.

        If ``persona_id`` is None, resolves to the user's default persona.
        ``force=True`` recomputes even when a row exists.
        """
        # Resolve persona (default if omitted) so callers don't have to.
        if persona_id is None:
            default = await self._personas.get_default(user_id)
            persona_id = default.id if default else None

        if not force:
            cached = await self._reports.get_for_pair(
                user_id=user_id, job_id=job_id, persona_id=persona_id
            )
            if cached is not None:
                return cached

        # ---- compute ------------------------------------------------------
        job = await self._jobs.get_by_id(user_id=user_id, job_id=job_id)
        if job is None:
            raise NotFoundError("Job not found")

        # Existing confidence pass — technical / architecture / domain etc.
        base = await self._confidence.build(user_id=user_id, job_id=job_id)

        # Re-fetch evidence so we can attach importance + status to missing
        # skills. JobConfidenceReport returns plain names; downstream wants
        # {name, importance, status} dicts.
        evidence_report = await self._evidence.build(
            user_id=user_id, job_id=job_id
        )
        evidence_by_name = {
            row.name.lower(): row for row in evidence_report.skills
        }
        missing_dicts: list[dict[str, object]] = []
        for name in base.missing_critical_skills:
            row = evidence_by_name.get(name.lower())
            missing_dicts.append(
                {
                    "name": name,
                    "importance": getattr(row, "importance", None) or 3,
                    "status": getattr(row, "status", "missing"),
                }
            )

        # Profile (drives version + weights downstream).
        profile = (
            await self._resolver.load_for_persona(
                user_id=user_id, persona_id=persona_id
            )
            if persona_id is not None
            else await self._resolver.load_for_user(user_id)
        )

        # Leadership + soft signals — only score when the job demands them.
        # Use the names from the missing list as one signal source.
        required_skills = [d["name"] for d in missing_dicts]
        # ALSO pull from the job description so we catch implicit demand.
        leadership_demand = detect_leadership_demand(
            description=job.description, required_skills=required_skills
        )
        soft_demand = detect_soft_demand(
            description=job.description, required_skills=required_skills
        )

        leadership_fit: int | None = None
        soft_fit: int | None = None
        if leadership_demand or soft_demand:
            # Build a (skill_id -> category) lookup so we can bucket the pot.
            pot = await self._user_skills.list_for_user(user_id)
            cat_by_id: dict[str, str] = {}
            for row in pot:
                entry = await self._catalog.get_by_id(row.skill_id)
                if entry is not None:
                    cat_by_id[str(row.skill_id)] = entry.category
            if leadership_demand:
                leadership_fit = score_category_fit(
                    user_skills=pot,
                    catalog_categories=cat_by_id,
                    target_categories={"leadership"},
                )
            if soft_demand:
                soft_fit = score_category_fit(
                    user_skills=pot,
                    catalog_categories=cat_by_id,
                    target_categories={"soft"},
                )

        # Recompute overall to fold in the new dimensions when present.
        overall = _recompute_overall(
            technical=base.technical_match,
            architecture=base.architecture_match,
            domain=base.domain_match,
            leadership=leadership_fit,
            soft=soft_fit,
        )

        # Gap recommendations from the missing-skill list. importance flows
        # through so high-importance gaps get priority 1.
        recommendations = self._recs.recommend(missing_skills=missing_dicts)

        report = MatchReport(
            id=uuid4(),
            user_id=user_id,
            job_id=job_id,
            persona_id=persona_id,
            overall_match=overall,
            technical_fit=base.technical_match,
            architecture_fit=base.architecture_match,
            domain_fit=base.domain_match,
            leadership_fit=leadership_fit,
            soft_skills_fit=soft_fit,
            interview_chance=base.interview_chance,
            missing_critical_skills=missing_dicts,
            missing_recommendations=recommendations,
            rationale=list(base.rationale or []),
            profile_version=profile.version,
        )
        # Persist (UPSERT by (job_id, persona_id)).
        return await self._reports.upsert(report, payload={})

    async def list_for_job(
        self, *, user_id: UUID, job_id: UUID
    ) -> list[MatchReport]:
        return await self._reports.list_for_job(user_id=user_id, job_id=job_id)


def _recompute_overall(
    *,
    technical: int,
    architecture: int,
    domain: int,
    leadership: int | None,
    soft: int | None,
) -> int:
    """Weighted overall that gracefully includes new dimensions only when present.

    Base coefficients: technical 0.50, architecture 0.30, domain 0.20.
    When leadership / soft are scored, they steal a small slice from
    architecture + domain so the headline reflects the broader fit.
    """
    if leadership is None and soft is None:
        return max(0, min(100, round(0.5 * technical + 0.3 * architecture + 0.2 * domain)))

    weights = {"technical": 0.45, "architecture": 0.25, "domain": 0.15}
    values: dict[str, int] = {
        "technical": technical,
        "architecture": architecture,
        "domain": domain,
    }
    extras: list[tuple[str, int]] = []
    if leadership is not None:
        extras.append(("leadership", leadership))
    if soft is not None:
        extras.append(("soft", soft))
    # Distribute remaining 0.15 across whichever extras exist.
    share = 0.15 / len(extras)
    for name, value in extras:
        weights[name] = share
        values[name] = value
    overall = sum(weights[k] * values[k] for k in weights)
    return max(0, min(100, round(overall)))
