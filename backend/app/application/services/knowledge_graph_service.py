from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from app.application.services.cv_structuring import (
    CvStructuredPayload,
    all_skill_names,
)
from app.application.services.skill_catalog_service import SkillCatalogService
from app.domain.repositories.experience_repository import ExperienceRepository
from app.domain.repositories.user_skill_repository import UserSkillRepository


def _parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except (TypeError, ValueError):
        return None


class KnowledgeGraphService:
    """High-level orchestrator over the per-user knowledge graph.

    Phase B exposed the skill pot. Phase D wires the wider graph: when a
    CV / LinkedIn / certificate ingest completes, ``ingest_from_cv`` writes
    experiences, links them to the catalog, and updates the user_skills pot
    with provenance tracked via ``sources.cv_upload_ids``.
    """

    def __init__(
        self,
        *,
        skill_catalog: SkillCatalogService,
        user_skills: UserSkillRepository,
        experiences: ExperienceRepository | None = None,
    ) -> None:
        self._skill_catalog = skill_catalog
        self._user_skills = user_skills
        self._experiences = experiences

    # ---- Skill-pot operations ---------------------------------------

    async def add_skill_evidence(
        self,
        *,
        user_id: UUID,
        raw_name: str,
        source_kind: str,
        source_id: UUID | str | None,
    ) -> None:
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

    # ---- CV ingest --------------------------------------------------

    async def ingest_from_cv(
        self,
        *,
        user_id: UUID,
        cv_upload_id: UUID,
        payload: CvStructuredPayload,
    ) -> dict[str, int]:
        """Write the structured CV into experiences + user_skills.

        Returns a tally so callers can surface "5 experiences, 23 skills"
        in the UI.

        Idempotent on re-ingest: experiences are matched by
        (lower(company), lower(role), start_date) and merged rather than
        duplicated; skill rows merge their sources via
        :func:`UserSkillRepository.upsert`.
        """
        if self._experiences is None:
            # Phase B users that haven't been migrated to the experience
            # repo yet — still grow the pot, just skip experiences.
            return await self._ingest_skills_only(
                user_id=user_id, cv_upload_id=cv_upload_id, payload=payload
            )

        experiences_written = 0
        skills_written = 0

        # ---- Resolve top-level skills first; we'll attach by name when an
        # experience mentions them.
        catalog_by_name: dict[str, UUID] = {}
        for raw_name in all_skill_names(payload):
            entry = await self._skill_catalog.resolve(raw_name)
            if entry is None:
                continue
            catalog_by_name[raw_name.lower()] = entry.id
            # Top-level skills land in the pot regardless of which experience
            # cited them.
            await self._user_skills.upsert(
                user_id=user_id,
                skill_id=entry.id,
                sources={"cv_upload_ids": [str(cv_upload_id)]},
            )
            skills_written += 1

        # ---- Experiences + their per-experience skill links.
        for exp in payload.experiences:
            skill_ids: list[UUID] = []
            for raw_name in exp.skills or []:
                resolved = catalog_by_name.get(raw_name.lower())
                if resolved is None:
                    entry = await self._skill_catalog.resolve(raw_name)
                    if entry is None:
                        continue
                    resolved = entry.id
                    catalog_by_name[raw_name.lower()] = resolved
                    await self._user_skills.upsert(
                        user_id=user_id,
                        skill_id=resolved,
                        sources={"cv_upload_ids": [str(cv_upload_id)]},
                    )
                if resolved not in skill_ids:
                    skill_ids.append(resolved)

            start_date = _parse_iso_date(exp.start_date)
            end_date = _parse_iso_date(exp.end_date)
            existing = await self._experiences.find_match(
                user_id=user_id,
                company=exp.company,
                role=exp.role,
                start_date=start_date,
            )
            if existing is not None:
                if skill_ids:
                    await self._experiences.add_skills(
                        experience_id=existing.id, skill_ids=skill_ids
                    )
                continue
            await self._experiences.create(
                user_id=user_id,
                company=exp.company,
                role=exp.role,
                location=exp.location,
                employment_type=exp.employment_type,
                start_date=start_date,
                end_date=end_date,
                summary=exp.summary,
                source="cv",
                source_ref=cv_upload_id,
                skill_ids=skill_ids,
                achievements=list(exp.achievements or []),
            )
            experiences_written += 1

        return {
            "experiences_written": experiences_written,
            "skills_touched": skills_written,
        }

    async def _ingest_skills_only(
        self,
        *,
        user_id: UUID,
        cv_upload_id: UUID,
        payload: CvStructuredPayload,
    ) -> dict[str, int]:
        skills_written = 0
        for raw_name in all_skill_names(payload):
            entry = await self._skill_catalog.resolve(raw_name)
            if entry is None:
                continue
            await self._user_skills.upsert(
                user_id=user_id,
                skill_id=entry.id,
                sources={"cv_upload_ids": [str(cv_upload_id)]},
            )
            skills_written += 1
        return {"experiences_written": 0, "skills_touched": skills_written}
