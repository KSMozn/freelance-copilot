"""Fetch a client URL, extract structured company research, persist on the job.

One AI call, schema-validated, stored on `jobs.client_research`. The proposal
generator can later quote `personalization_hook` to open with a specific read
of the client.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from pydantic import ValidationError

from app.application.dto.job_dto import CompanyResearchSchema
from app.domain.entities.job import CompanyResearch
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.providers.ai_provider import AIProvider
from app.domain.repositories.job_repository import JobRepository
from app.infrastructure.ai.errors import AIProviderError
from app.infrastructure.http.url_fetcher import UrlFetchError, fetch_page

logger = logging.getLogger(__name__)

RESEARCH_MARKER = "--- COMPANY RESEARCH ASSIGNMENT ---"

SYSTEM_PROMPT = """You are an analyst preparing concise client research for \
a freelance proposal.

Hard rules:
- Reply with a single JSON object matching the schema in the user prompt. \
  Output nothing else — no prose, no markdown, no code fences.
- Ground every field in the supplied page text. Do NOT invent products, \
  funding rounds, customer segments, or tech stack items.
- If a field can't be derived from the input, set it to null (or empty list \
  for `existing_stack`). Better empty than wrong.
- `personalization_hook` is ONE sentence the proposal can lead with, in the \
  voice of the writer — e.g. "I noticed your platform focuses on subscription \
  analytics for B2B SaaS — that's adjacent to a recent build."
- Keep each free-text field tight (≤ 60 words). `existing_stack` ≤ 8 items.
"""


class CompanyResearchFailedError(DomainError):
    """Raised when the URL can't be fetched or the AI response is unusable."""


def _build_user_prompt(*, source_url: str, title: str | None, description: str | None, text: str) -> str:
    return "\n".join(
        [
            RESEARCH_MARKER,
            f"Source URL: {source_url}",
            f"Page title: {title or '(none)'}",
            f"Meta description: {description or '(none)'}",
            "",
            "Page text:",
            text,
            "",
            "Return JSON only with these keys:",
            "{",
            '  "business_domain": string | null,        // 1–3 words',
            '  "product_summary": string | null,        // 1 sentence',
            '  "target_customers": string | null,       // who they sell to',
            '  "existing_stack": string[],              // visible technologies',
            '  "funding_signals": string | null,        // YC, Series A, etc.',
            '  "likely_architecture": string | null,    // 1 sentence',
            '  "personalization_hook": string | null    // 1 sentence',
            "}",
        ]
    )


class CompanyResearchService:
    def __init__(
        self,
        *,
        job_repo: JobRepository,
        ai_provider: AIProvider,
    ) -> None:
        self._jobs = job_repo
        self._ai = ai_provider

    async def research(
        self, *, user_id: UUID, job_id: UUID, url: str
    ) -> CompanyResearchSchema:
        job = await self._jobs.get_by_id(job_id, user_id=user_id)
        if job is None:
            raise NotFoundError("Job not found")

        try:
            page = await fetch_page(url)
        except UrlFetchError as exc:
            raise CompanyResearchFailedError(str(exc)) from exc

        prompt = _build_user_prompt(
            source_url=page.final_url,
            title=page.title,
            description=page.meta_description,
            text=page.text,
        )
        try:
            raw = await self._ai.complete_json(
                system_prompt=SYSTEM_PROMPT, user_prompt=prompt
            )
        except AIProviderError as exc:
            raise CompanyResearchFailedError(f"AI provider error: {exc}") from exc

        data = dict(raw.data)
        data["source_url"] = page.final_url
        data["fetched_at"] = datetime.now(UTC).isoformat()

        try:
            schema = CompanyResearchSchema.model_validate(data)
        except ValidationError as exc:
            raise CompanyResearchFailedError(
                f"AI response did not match the research schema: {exc.errors()[:3]}"
            ) from exc

        await self._jobs.update(
            job_id,
            user_id=user_id,
            fields={
                "client_research": {
                    "source_url": schema.source_url,
                    "business_domain": schema.business_domain,
                    "product_summary": schema.product_summary,
                    "target_customers": schema.target_customers,
                    "existing_stack": list(schema.existing_stack),
                    "funding_signals": schema.funding_signals,
                    "likely_architecture": schema.likely_architecture,
                    "personalization_hook": schema.personalization_hook,
                    "fetched_at": schema.fetched_at.isoformat()
                    if schema.fetched_at
                    else None,
                }
            },
        )
        return schema
