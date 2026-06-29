"""OutputGenerationService — unified, persona-aware artifact generator.

One service, one prompt-template module, one ``outputs`` table — but
seven output kinds today (cover letter / Upwork proposal / recruiter
reply / LinkedIn message / consulting proposal / screening answer /
tailored resume). Per-kind specialisation lives in
:mod:`output_prompts`, not in extra services or tables.

Pipeline:
  1. Resolve persona (default if omitted) + load its profile.
  2. Build a compact "what the user can claim" context: top user_skills
     (proficiency ≥ 4), most-recent experiences, top projects.
  3. Compose system + user prompts via ``output_prompts.system_prompt_for``
     + ``user_prompt_for``.
  4. Call the AI provider (mock recognises ``OUTPUT_MARKER``).
  5. Validate the response shape (Pydantic).
  6. Attach citations via ``CitationService``.
  7. Persist + return.
"""
from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ValidationError

from app.application.services.citation_service import CitationService, GraphSnapshot
from app.application.services.output_prompts import (
    system_prompt_for,
    user_prompt_for,
)
from app.application.services.persona_profile_resolver import PersonaProfileResolver
from app.domain.entities.output import Output, OutputKind
from app.domain.exceptions import NotFoundError
from app.domain.providers.ai_provider import AIProvider
from app.domain.repositories.experience_repository import ExperienceRepository
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.output_repository import OutputRepository
from app.domain.repositories.persona_repository import PersonaRepository
from app.domain.repositories.skill_catalog_repository import SkillCatalogRepository
from app.domain.repositories.user_skill_repository import UserSkillRepository
from app.infrastructure.ai.errors import AIProviderParseError


class _OutputPayload(BaseModel):
    title: str | None = None
    body_markdown: str = Field(min_length=1, max_length=20_000)


class OutputGenerationService:
    def __init__(
        self,
        *,
        ai_provider: AIProvider,
        outputs: OutputRepository,
        jobs: JobRepository,
        personas: PersonaRepository,
        resolver: PersonaProfileResolver,
        user_skills: UserSkillRepository,
        skill_catalog: SkillCatalogRepository,
        experiences: ExperienceRepository,
        citations: CitationService,
        # `projects` repo is not a hard dep — Phase F MVP accepts None and
        # cites without projects. Phase D wired the rows; Phase H or later
        # can attach a project repo and the citation set grows automatically.
        projects_provider=None,
    ) -> None:
        self._ai = ai_provider
        self._outputs = outputs
        self._jobs = jobs
        self._personas = personas
        self._resolver = resolver
        self._user_skills = user_skills
        self._catalog = skill_catalog
        self._experiences = experiences
        self._citations = citations
        self._projects_provider = projects_provider

    async def generate(
        self,
        *,
        user_id: UUID,
        kind: OutputKind,
        job_id: UUID | None = None,
        persona_id: UUID | None = None,
    ) -> Output:
        # Resolve persona — default if omitted.
        if persona_id is None:
            default = await self._personas.get_default(user_id)
            persona_id = default.id if default else None

        persona = (
            await self._personas.get(user_id, persona_id) if persona_id else None
        )

        # Profile drives tone + strategic priorities + version stamp.
        profile = (
            await self._resolver.load_for_persona(user_id=user_id, persona_id=persona_id)
            if persona_id is not None
            else await self._resolver.load_for_user(user_id)
        )

        # Load job context (optional — some kinds are job-less, e.g. a
        # standalone LinkedIn DM). Phase F MVP requires a job; the schema
        # tolerates NULL job_id so Phase J's "public persona page" can
        # generate kindless outputs later.
        job = None
        if job_id is not None:
            job = await self._jobs.get_by_id(user_id=user_id, job_id=job_id)
            if job is None:
                raise NotFoundError("Job not found")

        # Persona-aware evidence context.
        top_skills = await self._top_skill_names(user_id=user_id, persona=persona)
        experiences_list = await self._experiences.list_for_user(user_id)
        top_experiences = [
            f"{e.role} at {e.company}"
            + (f" ({e.start_date.year}–{e.end_date.year if e.end_date else 'present'})"
                if e.start_date else "")
            for e in experiences_list[:6]
        ]
        # Projects are optional today — see __init__ note.
        top_projects: list[str] = []
        if self._projects_provider is not None:
            try:
                projects = await self._projects_provider.list_for_user(user_id)
                top_projects = [p.name for p in projects[:8]]
            except Exception:
                top_projects = []

        # Compose prompts.
        tone = (
            (persona.proposal_tone if persona and persona.proposal_tone else None)
            or "pragmatic"
        )
        target_role = persona.target_role if persona else None
        system_prompt = system_prompt_for(
            kind,
            tone=tone,
            target_role=target_role,
            strategic_priorities=list(profile.strategic_priorities),
        )
        user_prompt = user_prompt_for(
            kind,
            job_title=(job.title if job else "Untitled job"),
            job_description=(job.description if job else ""),
            persona_name=(persona.name if persona else "Default"),
            persona_target_role=target_role,
            top_skills=top_skills,
            top_projects=top_projects,
            top_experiences=top_experiences,
        )

        # Call the AI provider.
        raw = await self._ai.complete_json(
            system_prompt=system_prompt, user_prompt=user_prompt
        )
        try:
            payload = _OutputPayload.model_validate(raw.data)
        except ValidationError as exc:
            raise AIProviderParseError(
                f"Output generation did not match the schema: {exc.errors()}"
            ) from exc

        # Attach citations.
        graph = GraphSnapshot(
            experiences=experiences_list,
            projects=[],  # filled later when projects_provider lands
            skills=[(sid, name) for sid, name in await self._skill_pairs(user_id=user_id)],
        )
        citations = self._citations.attach(
            body_markdown=payload.body_markdown, graph=graph
        )

        output = Output(
            id=uuid4(),
            user_id=user_id,
            persona_id=persona_id,
            job_id=job_id,
            kind=kind,
            title=payload.title,
            content_markdown=payload.body_markdown,
            content_html=None,
            citations=citations,
            metadata={"profile_version": profile.version},
            tone=tone,
            ai_provider=raw.provider,
            ai_model=raw.model,
        )
        return await self._outputs.create(output)

    # ---- helpers -----------------------------------------------------

    async def _top_skill_names(
        self, *, user_id: UUID, persona
    ) -> list[str]:
        rows = await self._user_skills.list_for_user(user_id)
        # Sort by proficiency desc — list_for_user already orders this way,
        # but be defensive against repo changes.
        rows.sort(key=lambda r: (-r.proficiency, -r.evidence_count))
        # Pinned persona skills get the top slot.
        pinned = {str(s) for s in (persona.pinned_skill_ids if persona else [])}

        names: list[str] = []
        for row in rows:
            entry = await self._catalog.get_by_id(row.skill_id)
            if entry is None:
                continue
            if str(row.skill_id) in pinned:
                names.insert(0, entry.name)
            elif row.proficiency >= 4:
                names.append(entry.name)
        # Dedupe in case insert + append produced duplicates.
        seen: dict[str, None] = {}
        for n in names:
            seen.setdefault(n, None)
        return list(seen.keys())

    async def _skill_pairs(self, *, user_id: UUID) -> list[tuple[UUID, str]]:
        rows = await self._user_skills.list_for_user(user_id)
        out: list[tuple[UUID, str]] = []
        for row in rows:
            entry = await self._catalog.get_by_id(row.skill_id)
            if entry is not None:
                out.append((entry.id, entry.name))
        return out

    async def list_for_user(
        self,
        *,
        user_id: UUID,
        job_id: UUID | None = None,
        kind: OutputKind | None = None,
    ) -> list[Output]:
        return await self._outputs.list_for_user(
            user_id=user_id, job_id=job_id, kind=kind
        )

    async def get(self, *, user_id: UUID, output_id: UUID) -> Output:
        row = await self._outputs.get(user_id=user_id, output_id=output_id)
        if row is None:
            raise NotFoundError("Output not found")
        return row

    async def delete(self, *, user_id: UUID, output_id: UUID) -> bool:
        return await self._outputs.delete(user_id=user_id, output_id=output_id)
