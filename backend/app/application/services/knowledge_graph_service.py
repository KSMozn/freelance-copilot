from __future__ import annotations

from typing import Any
from uuid import UUID

from app.application.services.skill_catalog_service import SkillCatalogService
from app.domain.repositories.user_skill_repository import UserSkillRepository


class KnowledgeGraphService:
    """High-level orchestrator over the per-user knowledge graph.

    Phase B exposes only the skill-pot side of the graph (experiences /
    projects are populated by the backfill migration and consumed by future
    services). Phase D will extend this with `ingest_from_cv`,
    `ingest_from_linkedin`, `add_certificate`, etc. — each writing into the
    same pot with provenance tracked via `UserSkill.sources`.
    """

    def __init__(
        self,
        *,
        skill_catalog: SkillCatalogService,
        user_skills: UserSkillRepository,
    ) -> None:
        self._skill_catalog = skill_catalog
        self._user_skills = user_skills

    async def add_skill_evidence(
        self,
        *,
        user_id: UUID,
        raw_name: str,
        source_kind: str,
        source_id: UUID | str | None,
    ) -> None:
        """Normalize ``raw_name`` and record one evidence row in the user's pot.

        ``source_kind`` keys the entry into the appropriate JSONB list, e.g.
        ``"repo_ids"``, ``"resume_ids"``, ``"portfolio_ids"``, ``"cv_upload_ids"``,
        ``"linkedin_snapshot_ids"``. Two boolean keys are also supported:
        ``"manual"`` and ``"ai_suggested"`` (set ``source_id=None`` for those).
        """
        catalog = await self._skill_catalog.resolve(raw_name)
        if catalog is None:
            return

        if source_kind in ("manual", "ai_suggested"):
            sources: dict[str, Any] = {source_kind: True}
        else:
            sources = {source_kind: [str(source_id)] if source_id else []}

        await self._user_skills.upsert(
            user_id=user_id,
            skill_id=catalog.id,
            sources=sources,
        )

    async def list_user_skills(self, user_id: UUID) -> list[dict[str, Any]]:
        """Return the user's active pot for read-only display."""
        rows = await self._user_skills.list_for_user(user_id)
        return [
            {
                "skill_id": str(row.skill_id),
                "proficiency": row.proficiency,
                "evidence_count": row.evidence_count,
                "sources": row.sources,
                "pinned": row.pinned,
            }
            for row in rows
        ]
