from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.dto.output_dto import (
    CitationRead,
    OutputGenerateRequest,
    OutputKindLiteral,
    OutputRead,
)
from app.application.services.output_generation_service import (
    OutputGenerationService,
)
from app.core.deps import CurrentUser, get_output_generation_service
from app.domain.entities.output import Output
from app.domain.exceptions import NotFoundError

router = APIRouter(tags=["outputs"])

OutputServiceDep = Annotated[
    OutputGenerationService, Depends(get_output_generation_service)
]


def _to_read(output: Output) -> OutputRead:
    return OutputRead(
        id=output.id,
        user_id=output.user_id,
        persona_id=output.persona_id,
        job_id=output.job_id,
        kind=output.kind,
        title=output.title,
        content_markdown=output.content_markdown,
        content_html=output.content_html,
        citations=[CitationRead(**asdict(c)) for c in output.citations],
        metadata=output.metadata,
        tone=output.tone,
        ai_provider=output.ai_provider,
        ai_model=output.ai_model,
        created_at=output.created_at,
    )


@router.post("/outputs", response_model=OutputRead, status_code=status.HTTP_201_CREATED)
async def generate_output(
    payload: OutputGenerateRequest,
    user: CurrentUser,
    service: OutputServiceDep,
) -> OutputRead:
    """Generate a new artifact of `kind`. Default persona resolved when omitted."""
    try:
        output = await service.generate(
            user_id=user.id,
            kind=payload.kind,
            job_id=payload.job_id,
            persona_id=payload.persona_id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return _to_read(output)


@router.get("/outputs", response_model=list[OutputRead])
async def list_outputs(
    user: CurrentUser,
    service: OutputServiceDep,
    job_id: UUID | None = None,
    kind: OutputKindLiteral | None = None,
) -> list[OutputRead]:
    rows = await service.list_for_user(user_id=user.id, job_id=job_id, kind=kind)
    return [_to_read(r) for r in rows]


@router.get("/outputs/{output_id}", response_model=OutputRead)
async def get_output(
    output_id: UUID,
    user: CurrentUser,
    service: OutputServiceDep,
) -> OutputRead:
    try:
        output = await service.get(user_id=user.id, output_id=output_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return _to_read(output)


@router.delete("/outputs/{output_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_output(
    output_id: UUID,
    user: CurrentUser,
    service: OutputServiceDep,
) -> None:
    ok = await service.delete(user_id=user.id, output_id=output_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Output not found"
        )
