from datetime import UTC, datetime
from uuid import UUID

import jwt

from app.application.dto.auth_dto import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    OtpVerifyRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserRead,
)
from app.application.services.email_otp_service import EmailOtpService
from app.application.services.persona_service import PersonaService
from app.application.services.refresh_token_manager import RefreshTokenManager
from app.core.security import decode_token, hash_password, verify_password
from app.domain.entities.user import User
from app.domain.exceptions import (
    AlreadyExistsError,
    InvalidCredentialsError,
    NotFoundError,
)
from app.domain.repositories.user_repository import UserRepository


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        otp_service: EmailOtpService | None = None,
        persona_service: PersonaService | None = None,
        refresh_tokens: RefreshTokenManager | None = None,
    ) -> None:
        self._users = user_repo
        self._otp = otp_service
        self._personas = persona_service
        self._refresh = refresh_tokens

    async def _issue_tokens(self, user_id: UUID) -> TokenPair:
        if self._refresh is None:
            raise RuntimeError("Refresh-token manager is not configured")
        access, refresh = await self._refresh.issue(user_id, "user")
        return TokenPair(access_token=access, refresh_token=refresh)

    @staticmethod
    def _to_read(user: User) -> UserRead:
        return UserRead(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            email_verified_at=user.email_verified_at,
            last_login_at=user.last_login_at,
            selected_persona_kind=user.selected_persona_kind,
        )

    async def register(self, payload: RegisterRequest) -> AuthResponse:
        existing = await self._users.get_by_email(payload.email)
        if existing is not None:
            raise AlreadyExistsError("Email already registered")
        user = await self._users.create(
            email=str(payload.email),
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            selected_persona_kind=payload.persona_kind,
        )
        await self._users.touch_last_login(user.id, datetime.now(UTC))
        return AuthResponse(
            user=self._to_read(user), tokens=await self._issue_tokens(user.id)
        )

    async def login(self, payload: LoginRequest) -> AuthResponse:
        user = await self._users.get_by_email(str(payload.email))
        if (
            user is None
            or user.password_hash is None
            or not verify_password(payload.password, user.password_hash)
        ):
            raise InvalidCredentialsError("Invalid email or password")
        if not user.is_active:
            raise InvalidCredentialsError("User is inactive")
        await self._users.touch_last_login(user.id, datetime.now(UTC))
        return AuthResponse(
            user=self._to_read(user), tokens=await self._issue_tokens(user.id)
        )

    async def refresh(self, payload: RefreshRequest) -> TokenPair:
        if self._refresh is None:
            raise RuntimeError("Refresh-token manager is not configured")
        try:
            data = decode_token(payload.refresh_token, "refresh")
        except jwt.InvalidTokenError as exc:
            raise InvalidCredentialsError("Invalid refresh token") from exc
        if data.get("pt") == "admin":
            raise InvalidCredentialsError("Not a user refresh token")
        user_id = UUID(data["sub"])
        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise InvalidCredentialsError("User not found or inactive")
        access, refresh = await self._refresh.rotate(data, "user", user.id)
        return TokenPair(access_token=access, refresh_token=refresh)

    async def logout(self, payload: LogoutRequest) -> None:
        """Revoke the session behind a refresh token. Best-effort and
        non-leaking: a malformed/expired/unknown token is a silent no-op."""
        if self._refresh is None:
            return
        try:
            data = decode_token(payload.refresh_token, "refresh")
        except jwt.InvalidTokenError:
            return
        await self._refresh.revoke_session(data)

    async def get_user_by_token(self, access_token: str) -> User:
        try:
            data = decode_token(access_token, "access")
        except jwt.InvalidTokenError as exc:
            raise InvalidCredentialsError("Invalid access token") from exc
        # Admin tokens live in a separate identity space. Refusing them
        # here means an admin JWT cannot be replayed against user routes.
        if data.get("pt") == "admin":
            raise InvalidCredentialsError("Not a user token")
        user = await self._users.get_by_id(UUID(data["sub"]))
        if user is None:
            raise NotFoundError("User not found")
        # A still-valid access token must not outlive a disable action.
        # Mirrors the login/refresh and admin-token paths, which all check
        # is_active — closing the up-to-60-min window where a disabled user
        # keeps API access.
        if not user.is_active:
            raise InvalidCredentialsError("User is inactive")
        return user

    # --- OTP flow (Phase A) ------------------------------------------------

    async def request_otp(
        self,
        *,
        email: str,
        purpose: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        if self._otp is None:
            raise RuntimeError("OTP service is not configured")
        # We always issue a code, even if the email isn't registered. That
        # keeps signup and sign-in indistinguishable from the outside, so an
        # attacker can't enumerate accounts via this endpoint.
        await self._otp.issue(
            email=email,
            purpose=purpose,  # type: ignore[arg-type]
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def verify_otp(self, payload: OtpVerifyRequest) -> AuthResponse:
        if self._otp is None:
            raise RuntimeError("OTP service is not configured")
        await self._otp.verify(
            email=str(payload.email),
            code=payload.code,
            purpose=payload.purpose,
        )

        now = datetime.now(UTC)
        user = await self._users.get_by_email(str(payload.email))
        if user is None:
            # First time we've seen this email — create the account.
            user = await self._users.create(
                email=str(payload.email),
                password_hash=None,
                full_name=payload.full_name,
                email_verified_at=now,
                selected_persona_kind=payload.persona_kind,
            )
        elif user.email_verified_at is None:
            await self._users.mark_email_verified(user.id, now)
            # Reload so the response shows the new verified_at.
            user = await self._users.get_by_id(user.id)  # type: ignore[assignment]

        if user is None or not user.is_active:
            raise InvalidCredentialsError("User is inactive")

        # Every OTP-verified account needs a default persona so the dashboard
        # has a working context. Idempotent — only creates one if absent.
        if self._personas is not None:
            try:
                await self._personas.ensure_primary(user.id)
            except Exception:
                # Failing to provision a persona should not block sign-in;
                # the user can create one from the UI on first visit.
                pass

        await self._users.touch_last_login(user.id, now)
        return AuthResponse(
            user=self._to_read(user), tokens=await self._issue_tokens(user.id)
        )
