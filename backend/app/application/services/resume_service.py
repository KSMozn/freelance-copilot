"""Resume CRUD + embedding-on-write.

Mirrors PortfolioService — same embed-on-write contract, same lazy
ensure_embedding for late provider switches. Kept separate (rather than
generic-ifying both) because the two domains carry different fields and the
templating helpers around them are quite different.
"""
from __future__ import annotations

from uuid import UUID

from app.application.dto.resume_dto import (
    ResumeCreate,
    ResumeListResponse,
    ResumeRead,
    ResumeUpdate,
)
from app.domain.entities.resume import Resume
from app.domain.exceptions import NotFoundError
from app.domain.providers.embedding_provider import EmbeddingProvider
from app.domain.repositories.embedding_repository import EmbeddingRepository
from app.domain.repositories.resume_repository import ResumeRepository

RESUME_OWNER_TYPE = "resume"


def _to_read(r: Resume) -> ResumeRead:
    return ResumeRead(
        id=r.id,
        user_id=r.user_id,
        title=r.title,
        target_role=r.target_role,
        summary=r.summary,
        seniority_level=r.seniority_level,
        primary_skills=list(r.primary_skills),
        secondary_skills=list(r.secondary_skills),
        industries=list(r.industries),
        domains=list(r.domains),
        achievements=list(r.achievements),
        project_highlights=list(r.project_highlights),
        keywords=list(r.keywords),
        notes=r.notes,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


class ResumeService:
    def __init__(
        self,
        *,
        resume_repo: ResumeRepository,
        embedding_repo: EmbeddingRepository,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self._resumes = resume_repo
        self._embeddings = embedding_repo
        self._provider = embedding_provider

    async def _embed_and_persist(self, resume: Resume) -> None:
        vector = await self._provider.embed(resume.embedding_text())
        await self._embeddings.upsert(
            owner_type=RESUME_OWNER_TYPE,
            owner_id=resume.id,
            model=self._provider.model_id,
            vector=vector,
        )

    async def create(self, user_id: UUID, payload: ResumeCreate) -> ResumeRead:
        resume = await self._resumes.create(
            user_id=user_id,
            title=payload.title,
            target_role=payload.target_role,
            summary=payload.summary,
            seniority_level=payload.seniority_level,
            primary_skills=list(payload.primary_skills),
            secondary_skills=list(payload.secondary_skills),
            industries=list(payload.industries),
            domains=list(payload.domains),
            achievements=list(payload.achievements),
            project_highlights=list(payload.project_highlights),
            keywords=list(payload.keywords),
            notes=payload.notes,
        )
        await self._embed_and_persist(resume)
        return _to_read(resume)

    async def get(self, user_id: UUID, resume_id: UUID) -> ResumeRead:
        resume = await self._resumes.get_by_id(resume_id, user_id=user_id)
        if resume is None:
            raise NotFoundError("Resume not found")
        return _to_read(resume)

    async def list(
        self,
        user_id: UUID,
        *,
        search: str | None,
        domain: str | None,
        skill: str | None,
        limit: int,
        offset: int,
    ) -> ResumeListResponse:
        items, total = await self._resumes.list_for_user(
            user_id,
            search=search,
            domain=domain,
            skill=skill,
            limit=limit,
            offset=offset,
        )
        return ResumeListResponse(
            items=[_to_read(r) for r in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update(
        self, user_id: UUID, resume_id: UUID, payload: ResumeUpdate
    ) -> ResumeRead:
        fields: dict[str, object] = {
            k: v for k, v in payload.model_dump(exclude_unset=True).items()
        }
        if not fields:
            return await self.get(user_id, resume_id)
        resume = await self._resumes.update(resume_id, user_id=user_id, fields=fields)
        if resume is None:
            raise NotFoundError("Resume not found")
        await self._embed_and_persist(resume)
        return _to_read(resume)

    async def delete(self, user_id: UUID, resume_id: UUID) -> None:
        existed = await self._resumes.delete(resume_id, user_id=user_id)
        if not existed:
            raise NotFoundError("Resume not found")
        await self._embeddings.delete(
            owner_type=RESUME_OWNER_TYPE, owner_id=resume_id
        )

    async def ensure_embedding(self, resume: Resume) -> list[float]:
        """Lazily embeds a resume under the current provider's model_id."""
        existing = await self._embeddings.get(
            owner_type=RESUME_OWNER_TYPE,
            owner_id=resume.id,
            model=self._provider.model_id,
        )
        if existing is not None:
            return existing
        vector = await self._provider.embed(resume.embedding_text())
        await self._embeddings.upsert(
            owner_type=RESUME_OWNER_TYPE,
            owner_id=resume.id,
            model=self._provider.model_id,
            vector=vector,
        )
        return vector
