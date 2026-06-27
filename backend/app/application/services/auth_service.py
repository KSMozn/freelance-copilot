from uuid import UUID

import jwt

from app.application.dto.auth_dto import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserRead,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.domain.entities.user import User
from app.domain.exceptions import (
    AlreadyExistsError,
    InvalidCredentialsError,
    NotFoundError,
)
from app.domain.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._users = user_repo

    @staticmethod
    def _tokens_for(user_id: UUID) -> TokenPair:
        return TokenPair(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
        )

    @staticmethod
    def _to_read(user: User) -> UserRead:
        return UserRead(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
        )

    async def register(self, payload: RegisterRequest) -> AuthResponse:
        existing = await self._users.get_by_email(payload.email)
        if existing is not None:
            raise AlreadyExistsError("Email already registered")
        user = await self._users.create(
            email=str(payload.email),
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
        )
        return AuthResponse(user=self._to_read(user), tokens=self._tokens_for(user.id))

    async def login(self, payload: LoginRequest) -> AuthResponse:
        user = await self._users.get_by_email(str(payload.email))
        if user is None or not verify_password(payload.password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
        if not user.is_active:
            raise InvalidCredentialsError("User is inactive")
        return AuthResponse(user=self._to_read(user), tokens=self._tokens_for(user.id))

    async def refresh(self, payload: RefreshRequest) -> TokenPair:
        try:
            data = decode_token(payload.refresh_token, "refresh")
        except jwt.InvalidTokenError as exc:
            raise InvalidCredentialsError("Invalid refresh token") from exc
        user_id = UUID(data["sub"])
        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise InvalidCredentialsError("User not found or inactive")
        return self._tokens_for(user.id)

    async def get_user_by_token(self, access_token: str) -> User:
        try:
            data = decode_token(access_token, "access")
        except jwt.InvalidTokenError as exc:
            raise InvalidCredentialsError("Invalid access token") from exc
        user = await self._users.get_by_id(UUID(data["sub"]))
        if user is None:
            raise NotFoundError("User not found")
        return user
