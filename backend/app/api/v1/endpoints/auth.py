from fastapi import APIRouter, HTTPException, Request, status

from app.application.dto.auth_dto import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    OtpRequestRequest,
    OtpRequestResponse,
    OtpVerifyRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserRead,
)
from app.core.deps import AuthServiceDep, CurrentUser, SettingsDep
from app.core.rate_limit import (
    client_ip,
    login_account_limiter,
    login_ip_limiter,
    otp_request_ip_limiter,
    otp_verify_limiter,
    refresh_ip_limiter,
)
from app.domain.exceptions import (
    AlreadyExistsError,
    InvalidCredentialsError,
    OtpInvalidError,
    RateLimitedError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, auth: AuthServiceDep) -> AuthResponse:
    try:
        return await auth.register(payload)
    except AlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest, auth: AuthServiceDep, request: Request
) -> AuthResponse:
    # Per-account is the spoof-proof guard against brute-forcing one target;
    # per-IP is defense-in-depth. Both run before the (slow) password verify.
    login_account_limiter.check(f"login:{str(payload.email).lower()}")
    login_ip_limiter.check(f"login:{client_ip(request)}")
    try:
        return await auth.login(payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshRequest, auth: AuthServiceDep, request: Request
) -> TokenPair:
    refresh_ip_limiter.check(f"refresh:{client_ip(request)}")
    try:
        return await auth.refresh(payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/request-code", response_model=OtpRequestResponse)
async def request_code(
    payload: OtpRequestRequest,
    auth: AuthServiceDep,
    settings: SettingsDep,
    request: Request,
) -> OtpRequestResponse:
    otp_request_ip_limiter.check(f"otp-request:{client_ip(request)}")
    try:
        await auth.request_otp(
            email=str(payload.email),
            purpose=payload.purpose,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except RateLimitedError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)
        ) from exc
    return OtpRequestResponse(
        sent=True, expires_in_minutes=settings.otp_expires_minutes
    )


@router.post("/verify-code", response_model=AuthResponse)
async def verify_code(
    payload: OtpVerifyRequest, auth: AuthServiceDep, request: Request
) -> AuthResponse:
    otp_verify_limiter.check(f"otp-verify:{str(payload.email).lower()}")
    otp_verify_limiter.check(f"otp-verify:{client_ip(request)}")
    try:
        return await auth.verify_otp(payload)
    except OtpInvalidError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc


@router.post("/logout", response_model=LogoutResponse)
async def logout(payload: LogoutRequest, auth: AuthServiceDep) -> LogoutResponse:
    # Revokes the refresh token's whole family server-side. Best-effort:
    # always 200 so it can't be used to probe token validity.
    await auth.logout(payload)
    return LogoutResponse()


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        email_verified_at=user.email_verified_at,
        last_login_at=user.last_login_at,
    )
