"""Application tracker service.

Orchestrates create-from-proposal (which gathers the full context + snapshot),
status transitions (validated by the state machine), and list/get/update/
delete operations. Every transition emits an `ApplicationHistory` row.
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from app.application.dto.application_dto import (
    ApplicationDetailsUpdate,
    ApplicationHistoryRead,
    ApplicationListResponse,
    ApplicationRead,
    CreateFromProposalRequest,
    StatusUpdateRequest,
)
from app.application.services.application_snapshot import build_snapshot
from app.application.services.portfolio_matching_service import (
    PortfolioMatchingService,
)
from app.application.services.resume_recommendation_service import (
    ResumeRecommendationService,
)
from app.domain.entities.application import (
    STATUS_TIMESTAMP_FIELD,
    Application,
    ApplicationStatus,
)
from app.domain.exceptions import AlreadyExistsError, DomainError, NotFoundError
from app.domain.repositories.analysis_repository import OpportunityScoreRepository
from app.domain.repositories.application_repository import (
    ApplicationHistoryRepository,
    ApplicationRepository,
)
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.portfolio_repository import PortfolioRepository
from app.domain.repositories.proposal_repository import ProposalRepository
from app.domain.repositories.resume_repository import ResumeRepository
from app.domain.services.application_state_machine import (
    allowed_next_statuses,
    validate_transition,
)


def _to_read(app: Application) -> ApplicationRead:
    return ApplicationRead(
        id=app.id,
        user_id=app.user_id,
        job_id=app.job_id,
        proposal_id=app.proposal_id,
        resume_id=app.resume_id,
        portfolio_ids=list(app.portfolio_ids),
        status=app.status.value,  # type: ignore[arg-type]
        applied_at=app.applied_at,
        viewed_at=app.viewed_at,
        interview_at=app.interview_at,
        offer_at=app.offer_at,
        won_at=app.won_at,
        rejected_at=app.rejected_at,
        withdrawn_at=app.withdrawn_at,
        completed_at=app.completed_at,
        contract_amount=app.contract_amount,
        client_response=app.client_response,
        rejection_reason=app.rejection_reason,
        notes=app.notes,
        snapshot=app.snapshot,
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


class ApplicationService:
    def __init__(
        self,
        *,
        application_repo: ApplicationRepository,
        history_repo: ApplicationHistoryRepository,
        job_repo: JobRepository,
        proposal_repo: ProposalRepository,
        resume_repo: ResumeRepository,
        portfolio_repo: PortfolioRepository,
        score_repo: OpportunityScoreRepository,
        portfolio_matching_service: PortfolioMatchingService,
        resume_recommendation_service: ResumeRecommendationService,
    ) -> None:
        self._apps = application_repo
        self._history = history_repo
        self._jobs = job_repo
        self._proposals = proposal_repo
        self._resumes = resume_repo
        self._portfolios = portfolio_repo
        self._scores = score_repo
        self._matching = portfolio_matching_service
        self._recs = resume_recommendation_service

    async def create_from_proposal(
        self,
        *,
        user_id: UUID,
        proposal_id: UUID,
        payload: CreateFromProposalRequest,
    ) -> ApplicationRead:
        proposal = await self._proposals.get_by_id(proposal_id, user_id=user_id)
        if proposal is None:
            raise NotFoundError("Proposal not found")

        # Duplicate-prevention: one active application per job.
        existing = await self._apps.find_active_for_job(
            user_id=user_id, job_id=proposal.job_id
        )
        if existing is not None:
            raise AlreadyExistsError(
                f"An active application already exists for this job (status='{existing.status}')."
            )

        job = await self._jobs.get_by_id(proposal.job_id, user_id=user_id)
        if job is None:
            # The FK on proposals.job_id should prevent this; if we got here,
            # the proposal references a job the user no longer owns.
            raise NotFoundError("Job linked to the proposal no longer exists.")

        score = await self._scores.get_by_job_id(proposal.job_id)
        resume = (
            await self._resumes.get_by_id(proposal.resume_id, user_id=user_id)
            if proposal.resume_id
            else None
        )
        portfolios = []
        for pid in proposal.portfolio_ids:
            pf = await self._portfolios.get_by_id(pid, user_id=user_id)
            if pf is not None:
                portfolios.append(pf)

        # Re-run matching + recommendation to capture the talking points /
        # positioning the user actually saw. These are cheap with cached
        # embeddings; if matching fails (e.g. analysis missing) we still
        # persist the application with a partial snapshot.
        portfolio_matches = None
        resume_recs = None
        try:
            portfolio_matches = await self._matching.match(
                user_id=user_id, job_id=proposal.job_id, top_n=10
            )
        except DomainError:
            portfolio_matches = None
        try:
            resume_recs = await self._recs.recommend(
                user_id=user_id, job_id=proposal.job_id, top_n=10
            )
        except DomainError:
            resume_recs = None

        snapshot = build_snapshot(
            job=job,
            score=score,
            proposal=proposal,
            resume=resume,
            portfolios=portfolios,
            portfolio_matches=portfolio_matches,
            resume_recs=resume_recs,
        )

        now = datetime.now(UTC)
        initial_status = ApplicationStatus(payload.status)
        applied_at = now if initial_status == ApplicationStatus.applied else None

        application = await self._apps.create(
            user_id=user_id,
            job_id=proposal.job_id,
            proposal_id=proposal.id,
            resume_id=proposal.resume_id,
            portfolio_ids=list(proposal.portfolio_ids),
            status=initial_status,
            applied_at=applied_at,
            snapshot=snapshot,
        )
        await self._history.create(
            application_id=application.id,
            user_id=user_id,
            from_status=None,
            to_status=initial_status.value,
            note=payload.note,
        )
        return _to_read(application)

    async def get(self, *, user_id: UUID, application_id: UUID) -> ApplicationRead:
        application = await self._apps.get_by_id(application_id, user_id=user_id)
        if application is None:
            raise NotFoundError("Application not found")
        return _to_read(application)

    async def list(
        self,
        *,
        user_id: UUID,
        status: ApplicationStatus | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> ApplicationListResponse:
        items, total = await self._apps.list_for_user(
            user_id, status=status, search=search, limit=limit, offset=offset
        )
        return ApplicationListResponse(
            items=[_to_read(a) for a in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update_status(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
        payload: StatusUpdateRequest,
    ) -> ApplicationRead:
        application = await self._apps.get_by_id(application_id, user_id=user_id)
        if application is None:
            raise NotFoundError("Application not found")

        # Capture the pre-update status by value — the repository's `update`
        # may mutate the same object in place (in-memory fakes do).
        from_status_value = application.status.value

        to_status = ApplicationStatus(payload.to_status)
        validate_transition(from_status=application.status, to_status=to_status)

        now = datetime.now(UTC)
        fields: dict[str, object] = {"status": to_status.value}
        ts_field = STATUS_TIMESTAMP_FIELD.get(to_status)
        if ts_field and getattr(application, ts_field) is None:
            # Only set the per-status timestamp the first time we enter it.
            fields[ts_field] = now

        updated = await self._apps.update(
            application_id, user_id=user_id, fields=fields
        )
        assert updated is not None  # we just read it
        await self._history.create(
            application_id=application.id,
            user_id=user_id,
            from_status=from_status_value,
            to_status=to_status.value,
            note=payload.note,
        )
        return _to_read(updated)

    async def update_details(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
        payload: ApplicationDetailsUpdate,
    ) -> ApplicationRead:
        fields: dict[str, object] = {
            k: v for k, v in payload.model_dump(exclude_unset=True).items()
        }
        if not fields:
            return await self.get(user_id=user_id, application_id=application_id)
        application = await self._apps.update(
            application_id, user_id=user_id, fields=fields
        )
        if application is None:
            raise NotFoundError("Application not found")
        return _to_read(application)

    async def get_history(
        self, *, user_id: UUID, application_id: UUID
    ) -> list[ApplicationHistoryRead]:
        # Verify ownership first so we don't leak existence via empty history.
        application = await self._apps.get_by_id(application_id, user_id=user_id)
        if application is None:
            raise NotFoundError("Application not found")
        rows = await self._history.list_for_application(application_id, user_id=user_id)
        return [
            ApplicationHistoryRead(
                id=r.id,
                application_id=r.application_id,
                user_id=r.user_id,
                from_status=r.from_status,
                to_status=r.to_status,
                note=r.note,
                created_at=r.created_at,
            )
            for r in rows
        ]

    async def delete(self, *, user_id: UUID, application_id: UUID) -> None:
        ok = await self._apps.delete(application_id, user_id=user_id)
        if not ok:
            raise NotFoundError("Application not found")

    @staticmethod
    def allowed_next_statuses_for(
        status: ApplicationStatus,
    ) -> list[str]:
        return sorted(s.value for s in allowed_next_statuses(status))
