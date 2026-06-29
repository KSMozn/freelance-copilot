"""Generate a STAR-format interview story for a scanned repository.

One AI call, JSON-validated against `StarStorySchema`, persisted on the
`repositories.star_story` JSONB column. Idempotent: regenerate overwrites.

The proposal flow can quote the `headline` as a one-liner; the four STAR
fields are the deeper bullets for interview prep / live calls.
"""
from __future__ import annotations

from uuid import UUID

from pydantic import ValidationError

from app.application.dto.repository_dto import (
    RepositoryRead,
    StarStorySchema,
)
from app.application.services.repository_service import RepositoryService, _to_read
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.providers.ai_provider import AIProvider
from app.domain.repositories.repository_store import RepositoryStore
from app.infrastructure.ai.errors import AIProviderError

STAR_MARKER = "--- STAR STORY ASSIGNMENT ---"

SYSTEM_PROMPT = """You are a senior engineer preparing concise STAR-format \
interview answers for proposal/interview reuse.

Hard rules:
- Reply with a single JSON object matching the schema in the user prompt. \
  Output nothing else — no prose, no markdown, no code fences.
- Be specific. Reference the actual stack and behaviors found in the repo. \
  Never invent technologies that aren't in the input.
- `result` MUST be concrete (an outcome, behavior change, or shipped \
  capability) — not aspirational.
- `headline` is one tight sentence the proposal can quote as a hook.
- Plain prose, no hype words, no first-person filler.
- Length targets per field: situation ≤ 60 words, task ≤ 40 words, \
  action ≤ 80 words, result ≤ 40 words.
"""


def _build_prompt(*, repo) -> str:
    """Compact context — only what the model needs to write grounded STAR."""
    lines: list[str] = [STAR_MARKER, f"Repository: {repo.owner}/{repo.name}"]
    if repo.description:
        lines.append(f"Description: {repo.description}")
    if repo.architecture_summary:
        lines.append(f"Architecture: {repo.architecture_summary}")
    if repo.business_domain:
        lines.append(f"Business domain: {repo.business_domain}")
    if repo.languages:
        lines.append(f"Languages: {', '.join(repo.languages.keys())}")
    if repo.frameworks:
        lines.append(f"Frameworks: {', '.join(repo.frameworks)}")
    if repo.databases:
        lines.append(f"Databases: {', '.join(repo.databases)}")
    if repo.authentication:
        lines.append(f"Authentication: {', '.join(repo.authentication)}")
    if repo.ai_providers:
        lines.append(f"AI providers: {', '.join(repo.ai_providers)}")
    if repo.cloud:
        lines.append(f"Cloud: {', '.join(repo.cloud)}")
    if repo.strengths:
        lines.append("Strengths:")
        lines.extend(f"  - {s}" for s in repo.strengths)
    if repo.highlights:
        lines.append("Highlights:")
        lines.extend(f"  - {h}" for h in repo.highlights)
    if repo.readme_excerpt:
        excerpt = repo.readme_excerpt[:1500].strip()
        lines.append("README excerpt:")
        lines.append(excerpt)
    lines.extend(
        [
            "",
            "Return JSON only with these keys:",
            "{",
            '  "headline": string,   // 1 tight sentence the proposal can quote',
            '  "situation": string,  // problem context grounded in the repo',
            '  "task": string,       // what you owned',
            '  "action": string,     // what you did — specific to the stack',
            '  "result": string      // concrete outcome',
            "}",
        ]
    )
    return "\n".join(lines)


class StarStoryGenerationFailedError(DomainError):
    """Raised when the AI response cannot be parsed into a STAR story."""


class RepositoryStarStoryService:
    def __init__(
        self,
        *,
        repository_store: RepositoryStore,
        repository_service: RepositoryService,
        ai_provider: AIProvider,
    ) -> None:
        self._store = repository_store
        self._svc = repository_service
        self._ai = ai_provider

    async def generate(self, *, user_id: UUID, repository_id: UUID) -> RepositoryRead:
        repo = await self._store.get_by_id(repository_id, user_id=user_id)
        if repo is None:
            raise NotFoundError("Repository not found")
        if repo.scan_status != "scanned":
            raise StarStoryGenerationFailedError(
                "Repository must be scanned before generating a STAR story."
            )

        try:
            raw = await self._ai.complete_json(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=_build_prompt(repo=repo),
            )
        except AIProviderError as exc:
            raise StarStoryGenerationFailedError(f"AI provider error: {exc}") from exc

        try:
            schema = StarStorySchema.model_validate(raw.data)
        except ValidationError as exc:
            raise StarStoryGenerationFailedError(
                f"AI response did not match the STAR schema: {exc.errors()[:3]}"
            ) from exc

        updated = await self._store.update(
            repository_id,
            user_id=user_id,
            fields={
                "star_story": {
                    "headline": schema.headline,
                    "situation": schema.situation,
                    "task": schema.task,
                    "action": schema.action,
                    "result": schema.result,
                }
            },
        )
        if updated is None:
            raise NotFoundError("Repository not found")
        return _to_read(updated)
