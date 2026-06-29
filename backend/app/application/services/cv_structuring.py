"""LLM-based CV structuring.

Takes extracted text and returns a strict JSON object the
``KnowledgeGraphService`` can ingest: experiences (with company, role,
dates, summary, skills, achievements), top-level skills, and a free-form
summary string.

Lives outside ``cv_ingest_service.py`` because the same prompt + schema
also drives LinkedIn snapshot structuring (Phase D) and could be reused
for any "parse a CV-like document" surface later.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.domain.providers.ai_provider import AIProvider
from app.infrastructure.ai.errors import AIProviderParseError

# Marker token routed by MockAIProvider (see _mock_cv_payload). Keeping the
# string literal here so the mock and producer agree without a circular
# import.
CV_INGEST_MARKER = "CV_INGEST_MARKER"

CV_SYSTEM_PROMPT = """\
You are extracting structured data from a candidate's CV / resume.

Return STRICT JSON. The top-level keys are:
  - "summary": a 1-2 sentence professional summary (string)
  - "experiences": array of work-history items, ordered most-recent first
  - "skills": array of distinct skill names mentioned anywhere in the CV

Each experience object has:
  - "company": string (required)
  - "role": string (required)
  - "location": string or null
  - "employment_type": one of "full_time" | "contract" | "freelance" | "internship" | "part_time" | null
  - "start_date": ISO date "YYYY-MM-DD" or null
  - "end_date": ISO date "YYYY-MM-DD" or null (use null for "current")
  - "summary": 1-3 sentences describing the role (string or null)
  - "skills": array of skill names exercised in this role
  - "achievements": array of measurable outcomes (strings; no metric parsing
    needed — just the statement, e.g. "Cut p95 latency from 800ms to 120ms")

Rules:
  - Use the CANONICAL skill name where obvious (e.g. "PostgreSQL", not "postgres").
  - Do not invent experiences or skills not present in the input text.
  - Omit fields entirely rather than emitting empty strings.
"""


class _ExperienceSchema(BaseModel):
    company: str = Field(min_length=1, max_length=255)
    role: str = Field(min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=160)
    employment_type: str | None = None
    start_date: str | None = None  # validated downstream when we parse it
    end_date: str | None = None
    summary: str | None = Field(default=None, max_length=4000)
    skills: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


class CvStructuredPayload(BaseModel):
    summary: str | None = None
    experiences: list[_ExperienceSchema] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)


async def structure_cv(
    *, ai_provider: AIProvider, extracted_text: str
) -> CvStructuredPayload:
    """Call the AI provider and validate the structured result.

    Truncate input to ~12K chars so single CVs never blow the prompt budget —
    most CVs sit well under that; outliers will lose trailing pages.
    """
    if not extracted_text or not extracted_text.strip():
        return CvStructuredPayload()

    user_prompt = (
        f"{CV_INGEST_MARKER}\n\n"
        "Structure the following CV text:\n\n"
        f"{extracted_text[:12000]}"
    )
    raw = await ai_provider.complete_json(
        system_prompt=CV_SYSTEM_PROMPT, user_prompt=user_prompt
    )
    try:
        return CvStructuredPayload.model_validate(raw.data)
    except ValidationError as exc:
        raise AIProviderParseError(
            f"CV structuring did not match the schema: {exc.errors()}"
        ) from exc


def empty_payload() -> CvStructuredPayload:
    return CvStructuredPayload()


def to_dict(payload: CvStructuredPayload) -> dict[str, Any]:
    """Stable JSONB shape for ``cv_uploads.extracted_structure``."""
    return payload.model_dump(mode="json")


def all_skill_names(payload: CvStructuredPayload) -> list[str]:
    """Flatten skills from the top-level list + per-experience lists, deduped."""
    seen: dict[str, None] = {}
    for s in payload.skills:
        if isinstance(s, str) and s.strip():
            seen.setdefault(s.strip(), None)
    for exp in payload.experiences:
        for s in exp.skills:
            if isinstance(s, str) and s.strip():
                seen.setdefault(s.strip(), None)
    return list(seen.keys())
