"""AdminAuthService — password-only login for the separate admin_users
identity space. No self-registration: admin accounts are seeded via the
`create_admin` script (Cloud Run job).
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import jwt

from app.application.dto.admin_auth_dto import (
    AdminAuthResponse,
    AdminLoginRequest,
    AdminRefreshRequest,
    AdminTokenPair,
    AdminUserRead,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.domain.entities.admin_user import AdminUser
from app.domain.exceptions import InvalidCredentialsError, NotFoundError
from app.infrastructure.db.repositories.sqlalchemy_admin_user_repository import (
    SQLAlchemyAdminUserRepository,
)


class AdminAuthService:
    def __init__(self, admin_repo: SQLAlchemyAdminUserRepository) -> None:
        self._admins = admin_repo

    @staticmethod
    def _tokens_for(admin_id: UUID) -> AdminTokenPair:
        return AdminTokenPair(
            access_token=create_access_token(admin_id, principal_type="admin"),
            refresh_token=create_refresh_token(admin_id, principal_type="admin"),
        )

    @staticmethod
    def _to_read(admin: AdminUser) -> AdminUserRead:
        return AdminUserRead(
            id=admin.id,
            email=admin.email,
            full_name=admin.full_name,
            is_active=admin.is_active,
            last_login_at=admin.last_login_at,
            created_at=admin.created_at,
        )

    async def login(self, payload: AdminLoginRequest) -> AdminAuthResponse:
        admin = await self._admins.get_by_email(str(payload.email))
        if admin is None or not verify_password(payload.password, admin.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
        if not admin.is_active:
            raise InvalidCredentialsError("Admin account is disabled")
        await self._admins.touch_last_login(admin.id, datetime.now(UTC))
        return AdminAuthResponse(
            user=self._to_read(admin), tokens=self._tokens_for(admin.id)
        )

    async def refresh(self, payload: AdminRefreshRequest) -> AdminTokenPair:
        try:
            data = decode_token(payload.refresh_token, "refresh")
        except jwt.InvalidTokenError as exc:
            raise InvalidCredentialsError("Invalid refresh token") from exc
        if data.get("pt") != "admin":
            raise InvalidCredentialsError("Not an admin refresh token")
        admin_id = UUID(data["sub"])
        admin = await self._admins.get_by_id(admin_id)
        if admin is None or not admin.is_active:
            raise InvalidCredentialsError("Admin not found or inactive")
        return self._tokens_for(admin.id)

    async def get_admin_by_token(self, access_token: str) -> AdminUser:
        try:
            data = decode_token(access_token, "access")
        except jwt.InvalidTokenError as exc:
            raise InvalidCredentialsError("Invalid access token") from exc
        if data.get("pt") != "admin":
            raise InvalidCredentialsError("Not an admin token")
        admin = await self._admins.get_by_id(UUID(data["sub"]))
        if admin is None:
            raise NotFoundError("Admin not found")
        return admin
