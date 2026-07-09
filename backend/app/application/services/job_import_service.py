"""Import a job by extracting fields from a screenshot.

Pipeline:
  validate image → call AIProvider.complete_json_with_image
                 → validate JobImportSchema
                 → compose description (summary + skills + questions)
                 → persist via JobService.create

Compose-on-import is deliberate: the existing Phase-2 analyzer reads
`Job.description`, so folding the structured extras (skills, questions,
project type) back into the description gives the analyzer the same
signal whether the job was pasted or screenshot-imported.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import ValidationError

from app.application.dto.job_dto import JobCreate
from app.application.dto.job_import_dto import (
    JobImportPreview,
    JobImportResponse,
    JobImportSchema,
)
from app.application.services.job_import_prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT,
)
from app.application.services.job_service import JobService
from app.domain.entities.job import BudgetType
from app.domain.exceptions import DomainError
from app.domain.providers.ai_provider import AIProvider
from app.infrastructure.ai.errors import AIProviderError

# Hard ceilings. Frontend enforces a friendlier client-side limit too.
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_IMAGE_MIME_TYPES: frozenset[str] = frozenset(
    {"image/png", "image/jpeg", "image/jpg", "image/webp"}
)


class JobImportFailedError(DomainError):
    """The provider response could not be validated as a job-import payload."""


class InvalidImageError(DomainError):
    """The image failed pre-flight validation (too large / wrong type / empty)."""


def _validate_image(*, image_bytes: bytes, mime_type: str) -> str:
    """Normalise the mime type + enforce limits. Returns the canonical mime type."""
    if not image_bytes:
        raise InvalidImageError("Empty image upload.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise InvalidImageError(
            f"Image is {len(image_bytes) / 1024 / 1024:.1f} MB, "
            f"max is {MAX_IMAGE_BYTES // 1024 // 1024} MB."
        )
    # image/jpg isn't strictly standard; normalise to image/jpeg
    canonical = "image/jpeg" if mime_type == "image/jpg" else mime_type
    if canonical not in ALLOWED_IMAGE_MIME_TYPES:
        raise InvalidImageError(
            f"Unsupported image type {mime_type!r}. "
            f"Accepted: {', '.join(sorted(ALLOWED_IMAGE_MIME_TYPES))}."
        )
    return canonical


def _build_description(schema: JobImportSchema) -> str:
    """Compose a single description block from the structured extraction.

    The summary text goes first verbatim, then a small structured trailer with
    project metadata, skills, and pre-application questions. The analyzer
    reads this whole block, so keeping the markers stable means Phase-2
    extraction works the same way for screenshot- and paste-imported jobs.
    """
    parts: list[str] = [schema.description.strip()]
    meta_lines: list[str] = []
    if schema.project_type:
        meta_lines.append(f"Project type: {schema.project_type}")
    if schema.project_duration:
        meta_lines.append(f"Duration: {schema.project_duration}")
    if schema.experience_level:
        meta_lines.append(f"Experience level: {schema.experience_level}")
    if schema.location:
        meta_lines.append(f"Location: {schema.location}")
    if schema.posted_at:
        meta_lines.append(f"Posted: {schema.posted_at}")
    if meta_lines:
        parts.append("\n".join(meta_lines))

    if schema.mandatory_skills:
        parts.append(
            "Mandatory skills: " + ", ".join(schema.mandatory_skills)
        )
    if schema.nice_to_have_skills:
        parts.append(
            "Nice-to-have skills: " + ", ".join(schema.nice_to_have_skills)
        )
    if schema.questions:
        question_block = "\n".join(f"- {q}" for q in schema.questions)
        parts.append("Pre-application questions:\n" + question_block)
    return "\n\n".join(parts)


class JobImportService:
    def __init__(
        self,
        *,
        ai_provider: AIProvider,
        job_service: JobService,
    ) -> None:
        self._ai = ai_provider
        self._jobs = job_service

    async def import_from_image(
        self,
        *,
        user_id: UUID,
        image_bytes: bytes,
        image_mime_type: str,
        source_url: str | None = None,
    ) -> JobImportResponse:
        mime_type = _validate_image(
            image_bytes=image_bytes, mime_type=image_mime_type
        )

        try:
            raw = await self._ai.complete_json_with_image(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=USER_PROMPT,
                image_bytes=image_bytes,
                image_mime_type=mime_type,
            )
        except AIProviderError as exc:
            raise JobImportFailedError(f"AI provider error: {exc}") from exc

        try:
            schema = JobImportSchema.model_validate(raw.data)
        except ValidationError as exc:
            raise JobImportFailedError(
                f"AI response did not match the import schema: {exc.errors()[:3]}"
            ) from exc

        if not schema.title.strip() or not schema.description.strip():
            raise JobImportFailedError(
                "Could not detect a job post in the screenshot. "
                "Make sure the image shows the full job title and summary."
            )

        # Caller-supplied URL beats whatever the model guessed (it's
        # explicit + verifiable).
        final_url = source_url or (str(schema.source_url) if schema.source_url else None)

        description = _build_description(schema)
        payload = JobCreate(
            title=schema.title.strip(),
            description=description,
            source_url=final_url,
            budget_type=BudgetType(schema.budget_type) if schema.budget_type else None,
            budget_min=_coerce_decimal(schema.budget_min),
            budget_max=_coerce_decimal(schema.budget_max),
            currency=schema.currency or "USD",
            proposal_count=schema.proposal_count,
        )
        job = await self._jobs.create(user_id, payload)

        preview = JobImportPreview(
            project_duration=schema.project_duration,
            project_type=schema.project_type,
            experience_level=schema.experience_level,
            location=schema.location,
            posted_at=schema.posted_at,
            mandatory_skills=list(schema.mandatory_skills),
            nice_to_have_skills=list(schema.nice_to_have_skills),
            questions=list(schema.questions),
        )
        return JobImportResponse(
            job=job,
            preview=preview,
            provider=raw.provider,
            model=raw.model,
        )


def _coerce_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (ArithmeticError, ValueError, TypeError):
        return None
