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
    AdminLogoutRequest,
    AdminRefreshRequest,
    AdminTokenPair,
    AdminUserRead,
)
from app.application.services.refresh_token_manager import RefreshTokenManager
from app.core.security import decode_token, verify_password
from app.domain.entities.admin_user import AdminUser
from app.domain.exceptions import InvalidCredentialsError, NotFoundError
from app.infrastructure.db.repositories.sqlalchemy_admin_user_repository import (
    SQLAlchemyAdminUserRepository,
)


class AdminAuthService:
    def __init__(
        self,
        admin_repo: SQLAlchemyAdminUserRepository,
        refresh_tokens: RefreshTokenManager | None = None,
    ) -> None:
        self._admins = admin_repo
        self._refresh = refresh_tokens

    async def _issue_tokens(self, admin_id: UUID) -> AdminTokenPair:
        if self._refresh is None:
            raise RuntimeError("Refresh-token manager is not configured")
        access, refresh = await self._refresh.issue(admin_id, "admin")
        return AdminTokenPair(access_token=access, refresh_token=refresh)

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
            user=self._to_read(admin), tokens=await self._issue_tokens(admin.id)
        )

    async def refresh(self, payload: AdminRefreshRequest) -> AdminTokenPair:
        if self._refresh is None:
            raise RuntimeError("Refresh-token manager is not configured")
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
        access, refresh = await self._refresh.rotate(data, "admin", admin.id)
        return AdminTokenPair(access_token=access, refresh_token=refresh)

    async def logout(self, payload: AdminLogoutRequest) -> None:
        if self._refresh is None:
            return
        try:
            data = decode_token(payload.refresh_token, "refresh")
        except jwt.InvalidTokenError:
            return
        # Only revoke if it really is an admin refresh token.
        if data.get("pt") != "admin":
            return
        await self._refresh.revoke_session(data)

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
