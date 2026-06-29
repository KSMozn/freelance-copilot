from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.dto.persona_dto import (
    PersonaArchetypeRead,
    PersonaCreate,
    PersonaRead,
    PersonaUpdate,
)
from app.application.services.persona_service import PersonaService
from app.core.deps import CurrentUser, get_persona_service
from app.domain.entities.persona import Persona, PersonaArchetype
from app.domain.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    PermissionDeniedError,
)

router = APIRouter(prefix="/personas", tags=["personas"])

PersonaServiceDep = Annotated[PersonaService, Depends(get_persona_service)]


def _persona_to_read(p: Persona) -> PersonaRead:
    return PersonaRead(
        id=p.id,
        user_id=p.user_id,
        archetype_id=p.archetype_id,
        name=p.name,
        target_role=p.target_role,
        target_seniority=p.target_seniority,
        weights=p.weights,
        skill_category_weights=p.skill_category_weights,
        proposal_tone=p.proposal_tone,
        strategic_priorities=list(p.strategic_priorities),
        pinned_experience_ids=[str(x) for x in p.pinned_experience_ids],
        pinned_project_ids=[str(x) for x in p.pinned_project_ids],
        pinned_skill_ids=[str(x) for x in p.pinned_skill_ids],
        accent_color=p.accent_color,
        is_default=p.is_default,
        is_archived=p.is_archived,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _archetype_to_read(a: PersonaArchetype) -> PersonaArchetypeRead:
    return PersonaArchetypeRead(
        id=a.id,
        slug=a.slug,
        name=a.name,
        description=a.description,
        default_weights=a.default_weights,
        default_skill_category_weights=a.default_skill_category_weights,
        default_proposal_tone=a.default_proposal_tone,
        default_target_roles=a.default_target_roles,
        default_seniority_band=a.default_seniority_band,
        sort_order=a.sort_order,
    )


@router.get("/archetypes", response_model=list[PersonaArchetypeRead])
async def list_archetypes(
    _: CurrentUser, service: PersonaServiceDep
) -> list[PersonaArchetypeRead]:
    return [_archetype_to_read(a) for a in await service.list_archetypes()]


@router.get("", response_model=list[PersonaRead])
async def list_personas(
    user: CurrentUser, service: PersonaServiceDep
) -> list[PersonaRead]:
    return [_persona_to_read(p) for p in await service.list_for_user(user.id)]


@router.get("/current", response_model=PersonaRead)
async def get_current_persona(
    user: CurrentUser, service: PersonaServiceDep
) -> PersonaRead:
    # Idempotent — creates a Primary on the fly if the user somehow lacks one
    # (older accounts that pre-date Phase C, or a failed backfill).
    persona = await service.ensure_primary(user.id)
    return _persona_to_read(persona)


@router.post("", response_model=PersonaRead, status_code=status.HTTP_201_CREATED)
async def create_persona(
    payload: PersonaCreate,
    user: CurrentUser,
    service: PersonaServiceDep,
) -> PersonaRead:
    try:
        created = await service.instantiate_from_archetype(
            user_id=user.id,
            archetype_slug=payload.archetype_slug,
            name=payload.name,
            target_role=payload.target_role,
            is_default=payload.is_default,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except AlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return _persona_to_read(created)


@router.get("/{persona_id}", response_model=PersonaRead)
async def get_persona(
    persona_id: UUID,
    user: CurrentUser,
    service: PersonaServiceDep,
) -> PersonaRead:
    try:
        persona = await service.get(user.id, persona_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return _persona_to_read(persona)


@router.patch("/{persona_id}", response_model=PersonaRead)
async def update_persona(
    persona_id: UUID,
    payload: PersonaUpdate,
    user: CurrentUser,
    service: PersonaServiceDep,
) -> PersonaRead:
    patch = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    try:
        updated = await service.update(
            user_id=user.id, persona_id=persona_id, patch=patch
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return _persona_to_read(updated)


@router.post("/{persona_id}/set-default", response_model=PersonaRead)
async def set_default_persona(
    persona_id: UUID,
    user: CurrentUser,
    service: PersonaServiceDep,
) -> PersonaRead:
    try:
        persona = await service.set_default(user.id, persona_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return _persona_to_read(persona)


@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_persona(
    persona_id: UUID,
    user: CurrentUser,
    service: PersonaServiceDep,
) -> None:
    try:
        await service.delete(user.id, persona_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
