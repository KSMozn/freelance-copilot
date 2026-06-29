from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.application.dto.ingestion_dto import (
    CertificateCreate,
    CertificateRead,
    CertificateUpdate,
)
from app.core.deps import CurrentUser, SessionDep
from app.domain.entities.ingestion import CertificateEntry
from app.infrastructure.db.repositories.sqlalchemy_ingestion_repositories import (
    SQLAlchemyCertificateRepository,
)

router = APIRouter(prefix="/certificates", tags=["ingestion"])


def _to_read(c: CertificateEntry) -> CertificateRead:
    return CertificateRead(
        id=c.id,
        user_id=c.user_id,
        name=c.name,
        issuer=c.issuer,
        issued_date=c.issued_date,
        expiry_date=c.expiry_date,
        credential_id=c.credential_id,
        credential_url=c.credential_url,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.get("", response_model=list[CertificateRead])
async def list_certificates(
    user: CurrentUser, session: SessionDep
) -> list[CertificateRead]:
    repo = SQLAlchemyCertificateRepository(session)
    return [_to_read(r) for r in await repo.list_for_user(user.id)]


@router.post("", response_model=CertificateRead, status_code=status.HTTP_201_CREATED)
async def create_certificate(
    payload: CertificateCreate, user: CurrentUser, session: SessionDep
) -> CertificateRead:
    repo = SQLAlchemyCertificateRepository(session)
    cert = await repo.create(
        user_id=user.id,
        name=payload.name,
        issuer=payload.issuer,
        issued_date=payload.issued_date,
        expiry_date=payload.expiry_date,
        credential_id=payload.credential_id,
        credential_url=str(payload.credential_url) if payload.credential_url else None,
    )
    return _to_read(cert)


@router.patch("/{certificate_id}", response_model=CertificateRead)
async def update_certificate(
    certificate_id: UUID,
    payload: CertificateUpdate,
    user: CurrentUser,
    session: SessionDep,
) -> CertificateRead:
    repo = SQLAlchemyCertificateRepository(session)
    patch = payload.model_dump(exclude_unset=True)
    if "credential_url" in patch and patch["credential_url"] is not None:
        patch["credential_url"] = str(patch["credential_url"])
    cert = await repo.update(user_id=user.id, certificate_id=certificate_id, patch=patch)
    if cert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    return _to_read(cert)


@router.delete("/{certificate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certificate(
    certificate_id: UUID, user: CurrentUser, session: SessionDep
) -> None:
    repo = SQLAlchemyCertificateRepository(session)
    ok = await repo.delete(user_id=user.id, certificate_id=certificate_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
