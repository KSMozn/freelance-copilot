import hashlib
import re
from uuid import UUID

from app.application.dto.analysis_dto import OpportunityScoreRead
from app.application.dto.job_dto import JobCreate, JobListResponse, JobRead, JobUpdate
from app.domain.entities.analysis import OpportunityScore
from app.domain.entities.job import Job, JobStatus
from app.domain.exceptions import NotFoundError
from app.domain.repositories.job_repository import JobRepository


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _hash_description(description: str) -> str:
    return hashlib.sha256(_normalize(description).encode("utf-8")).hexdigest()


def _to_read(job: Job, score: OpportunityScore | None = None) -> JobRead:
    read = JobRead.model_validate(job)
    if score is not None:
        read = read.model_copy(update={"opportunity_score": OpportunityScoreRead.model_validate(score)})
    return read


class JobService:
    def __init__(self, job_repo: JobRepository) -> None:
        self._jobs = job_repo

    async def create(self, user_id: UUID, payload: JobCreate) -> JobRead:
        job = await self._jobs.create(
            user_id=user_id,
            title=payload.title,
            description=payload.description,
            source_hash=_hash_description(payload.description),
            source_url=str(payload.source_url) if payload.source_url else None,
            budget_type=payload.budget_type,
            budget_min=payload.budget_min,
            budget_max=payload.budget_max,
            currency=payload.currency,
            proposal_count=payload.proposal_count,
            status=JobStatus.new,
        )
        return _to_read(job)

    async def get(self, user_id: UUID, job_id: UUID) -> JobRead:
        job = await self._jobs.get_by_id(job_id, user_id=user_id)
        if job is None:
            raise NotFoundError("Job not found")
        return _to_read(job)

    async def list(
        self,
        user_id: UUID,
        *,
        status: JobStatus | None,
        limit: int,
        offset: int,
        search: str | None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> JobListResponse:
        items, total = await self._jobs.list_for_user(
            user_id,
            status=status,
            limit=limit,
            offset=offset,
            search=search,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        return JobListResponse(
            items=[_to_read(j, s) for j, s in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update(self, user_id: UUID, job_id: UUID, payload: JobUpdate) -> JobRead:
        fields: dict[str, object] = {}
        for k, v in payload.model_dump(exclude_unset=True).items():
            if k == "source_url" and v is not None:
                fields[k] = str(v)
            else:
                fields[k] = v
        if not fields:
            return await self.get(user_id, job_id)
        job = await self._jobs.update(job_id, user_id=user_id, fields=fields)
        if job is None:
            raise NotFoundError("Job not found")
        return _to_read(job)

    async def delete(self, user_id: UUID, job_id: UUID) -> None:
        ok = await self._jobs.delete(job_id, user_id=user_id)
        if not ok:
            raise NotFoundError("Job not found")
