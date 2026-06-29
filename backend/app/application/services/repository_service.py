"""CRUD + scan-and-embed lifecycle for scanned GitHub repositories.

Mirrors PortfolioService: every successful scan re-embeds; lazy
`ensure_embedding` covers repositories created before the current embedding
provider was selected.
"""
from __future__ import annotations

import logging
from uuid import UUID

from app.application.dto.repository_dto import (
    RepositoryListResponse,
    RepositoryRead,
    StarStorySchema,
)
from app.application.services.repository_scan_service import RepositoryScanService
from app.domain.entities.repository import Repository, StarStory
from app.domain.exceptions import NotFoundError
from app.domain.providers.embedding_provider import EmbeddingProvider
from app.domain.repositories.embedding_repository import EmbeddingRepository
from app.domain.repositories.repository_store import RepositoryStore
from app.infrastructure.github.github_client import parse_github_url

REPOSITORY_OWNER_TYPE = "repository"

logger = logging.getLogger(__name__)


class DuplicateRepositoryError(Exception):
    """Raised when the user tries to register the same github_url twice."""


def _to_read(r: Repository) -> RepositoryRead:
    return RepositoryRead(
        id=r.id,
        user_id=r.user_id,
        github_url=r.github_url,
        owner=r.owner,
        name=r.name,
        default_branch=r.default_branch,
        description=r.description,
        languages=dict(r.languages),
        frameworks=list(r.frameworks),
        libraries=list(r.libraries),
        databases=list(r.databases),
        authentication=list(r.authentication),
        ai_providers=list(r.ai_providers),
        cloud=list(r.cloud),
        ci_systems=list(r.ci_systems),
        test_frameworks=list(r.test_frameworks),
        has_docker=r.has_docker,
        has_ci=r.has_ci,
        has_tests=r.has_tests,
        architecture_summary=r.architecture_summary,
        business_domain=r.business_domain,
        strengths=list(r.strengths),
        highlights=list(r.highlights),
        readme_excerpt=r.readme_excerpt,
        scan_status=r.scan_status,
        scan_error=r.scan_error,
        scanned_at=r.scanned_at,
        star_story=(
            StarStorySchema(
                headline=r.star_story.headline,
                situation=r.star_story.situation,
                task=r.star_story.task,
                action=r.star_story.action,
                result=r.star_story.result,
            )
            if r.star_story
            else None
        ),
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


class RepositoryService:
    def __init__(
        self,
        *,
        repository_store: RepositoryStore,
        embedding_repo: EmbeddingRepository,
        embedding_provider: EmbeddingProvider,
        scan_service: RepositoryScanService,
    ) -> None:
        self._store = repository_store
        self._embeddings = embedding_repo
        self._provider = embedding_provider
        self._scan = scan_service

    async def create_and_scan(
        self,
        *,
        user_id: UUID,
        github_url: str,
        scan_now: bool = True,
    ) -> RepositoryRead:
        url = github_url.strip()
        try:
            owner, name = parse_github_url(url)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

        existing = await self._store.get_by_github_url(url, user_id=user_id)
        if existing is not None:
            raise DuplicateRepositoryError(
                f"Repository already registered: {existing.owner}/{existing.name}"
            )

        repo = await self._store.create(
            user_id=user_id,
            github_url=url,
            owner=owner,
            name=name,
        )

        if scan_now:
            repo = await self._run_scan(repo)
        return _to_read(repo)

    async def get(self, user_id: UUID, repository_id: UUID) -> RepositoryRead:
        repo = await self._store.get_by_id(repository_id, user_id=user_id)
        if repo is None:
            raise NotFoundError("Repository not found")
        return _to_read(repo)

    async def list(
        self,
        user_id: UUID,
        *,
        search: str | None,
        limit: int,
        offset: int,
    ) -> RepositoryListResponse:
        items, total = await self._store.list_for_user(
            user_id, search=search, limit=limit, offset=offset
        )
        return RepositoryListResponse(
            items=[_to_read(r) for r in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def rescan(self, user_id: UUID, repository_id: UUID) -> RepositoryRead:
        repo = await self._store.get_by_id(repository_id, user_id=user_id)
        if repo is None:
            raise NotFoundError("Repository not found")
        repo = await self._run_scan(repo)
        return _to_read(repo)

    async def delete(self, user_id: UUID, repository_id: UUID) -> None:
        existed = await self._store.delete(repository_id, user_id=user_id)
        if not existed:
            raise NotFoundError("Repository not found")
        await self._embeddings.delete(
            owner_type=REPOSITORY_OWNER_TYPE, owner_id=repository_id
        )

    async def ensure_embedding(self, repository: Repository) -> list[float]:
        existing = await self._embeddings.get(
            owner_type=REPOSITORY_OWNER_TYPE,
            owner_id=repository.id,
            model=self._provider.model_id,
        )
        if existing is not None:
            return existing
        vector = await self._provider.embed(repository.embedding_text())
        await self._embeddings.upsert(
            owner_type=REPOSITORY_OWNER_TYPE,
            owner_id=repository.id,
            model=self._provider.model_id,
            vector=vector,
        )
        return vector

    async def _run_scan(self, repo: Repository) -> Repository:
        try:
            result = await self._scan.scan(owner=repo.owner, name=repo.name)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "scan failed for %s/%s: %s", repo.owner, repo.name, exc
            )
            updated = await self._store.update(
                repo.id,
                user_id=repo.user_id,
                fields={
                    "scan_status": "failed",
                    "scan_error": str(exc)[:1000],
                },
            )
            return updated or repo

        updated = await self._store.update(
            repo.id, user_id=repo.user_id, fields=result.as_update_fields()
        )
        if updated is None:
            return repo
        await self._embed_and_persist(updated)
        return updated

    async def _embed_and_persist(self, repository: Repository) -> None:
        vector = await self._provider.embed(repository.embedding_text())
        await self._embeddings.upsert(
            owner_type=REPOSITORY_OWNER_TYPE,
            owner_id=repository.id,
            model=self._provider.model_id,
            vector=vector,
        )
