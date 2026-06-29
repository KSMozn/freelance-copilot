from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.application.dto.ingestion_dto import (
    ContentItemCreate,
    ContentItemRead,
    ContentItemUpdate,
)
from app.core.deps import CurrentUser, SessionDep
from app.domain.entities.ingestion import ContentItemEntry
from app.infrastructure.db.repositories.sqlalchemy_ingestion_repositories import (
    SQLAlchemyContentItemRepository,
)

router = APIRouter(prefix="/content-items", tags=["ingestion"])


def _to_read(c: ContentItemEntry) -> ContentItemRead:
    return ContentItemRead(
        id=c.id,
        user_id=c.user_id,
        type=c.type,
        title=c.title,
        url=c.url,
        published_date=c.published_date,
        summary=c.summary,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.get("", response_model=list[ContentItemRead])
async def list_content(
    user: CurrentUser, session: SessionDep
) -> list[ContentItemRead]:
    repo = SQLAlchemyContentItemRepository(session)
    return [_to_read(r) for r in await repo.list_for_user(user.id)]


@router.post("", response_model=ContentItemRead, status_code=status.HTTP_201_CREATED)
async def create_content(
    payload: ContentItemCreate, user: CurrentUser, session: SessionDep
) -> ContentItemRead:
    repo = SQLAlchemyContentItemRepository(session)
    item = await repo.create(
        user_id=user.id,
        type=payload.type,
        title=payload.title,
        url=str(payload.url) if payload.url else None,
        published_date=payload.published_date,
        summary=payload.summary,
        raw_text=payload.raw_text,
    )
    return _to_read(item)


@router.patch("/{content_id}", response_model=ContentItemRead)
async def update_content(
    content_id: UUID,
    payload: ContentItemUpdate,
    user: CurrentUser,
    session: SessionDep,
) -> ContentItemRead:
    repo = SQLAlchemyContentItemRepository(session)
    patch = payload.model_dump(exclude_unset=True)
    if "url" in patch and patch["url"] is not None:
        patch["url"] = str(patch["url"])
    item = await repo.update(user_id=user.id, content_id=content_id, patch=patch)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content item not found")
    return _to_read(item)


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: UUID, user: CurrentUser, session: SessionDep
) -> None:
    repo = SQLAlchemyContentItemRepository(session)
    ok = await repo.delete(user_id=user.id, content_id=content_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content item not found")
