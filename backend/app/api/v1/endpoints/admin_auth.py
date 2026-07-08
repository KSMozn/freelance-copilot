"""Admin auth endpoints — /api/v1/admin/auth/*.

Login-only surface. No self-registration; admin_users are seeded via the
`create_admin` Cloud Run job.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.application.dto.admin_auth_dto import (
    AdminAuthResponse,
    AdminLoginRequest,
    AdminRefreshRequest,
    AdminTokenPair,
    AdminUserRead,
)
from app.application.services.admin_auth_service import AdminAuthService
from app.core.deps import CurrentAdmin, SessionDep
from app.core.rate_limit import (
    client_ip,
    login_account_limiter,
    login_ip_limiter,
    refresh_ip_limiter,
)
from app.domain.exceptions import InvalidCredentialsError
from app.infrastructure.db.repositories.sqlalchemy_admin_user_repository import (
    SQLAlchemyAdminUserRepository,
)

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])


def _service(session: SessionDep) -> AdminAuthService:
    return AdminAuthService(SQLAlchemyAdminUserRepository(session))


AdminAuthDep = Annotated[AdminAuthService, Depends(_service)]


@router.post("/login", response_model=AdminAuthResponse)
async def login(
    payload: AdminLoginRequest, auth: AdminAuthDep, request: Request
) -> AdminAuthResponse:
    # Admin login is password-only with no MFA — throttle it hardest. Keyed
    # on the target email (spoof-proof) and the source IP.
    login_account_limiter.check(f"admin-login:{str(payload.email).lower()}")
    login_ip_limiter.check(f"admin-login:{client_ip(request)}")
    try:
        return await auth.login(payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc


@router.post("/refresh", response_model=AdminTokenPair)
async def refresh(
    payload: AdminRefreshRequest, auth: AdminAuthDep, request: Request
) -> AdminTokenPair:
    refresh_ip_limiter.check(f"admin-refresh:{client_ip(request)}")
    try:
        return await auth.refresh(payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc


@router.get("/me", response_model=AdminUserRead)
async def me(admin: CurrentAdmin) -> AdminUserRead:
    return AdminUserRead(
        id=admin.id,
        email=admin.email,
        full_name=admin.full_name,
        is_active=admin.is_active,
        last_login_at=admin.last_login_at,
        created_at=admin.created_at,
    )
