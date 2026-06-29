from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    email_verified_at: datetime | None = None
    last_login_at: datetime | None = None


class AuthResponse(BaseModel):
    user: UserRead
    tokens: TokenPair


# --- OTP (Phase A) ---------------------------------------------------------


class OtpRequestRequest(BaseModel):
    """Ask the server to send a 6-digit code to the given email."""

    email: EmailStr
    # 'login' if user already exists, 'register' if signing up. The server
    # accepts either — we don't leak account existence by erroring early.
    purpose: Literal["login", "register"] = "login"


class OtpRequestResponse(BaseModel):
    sent: bool = True
    expires_in_minutes: int


class OtpVerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    # For register, the server creates the account if it doesn't exist.
    purpose: Literal["login", "register"] = "login"
    # Only used on register: optional display name to save on the new user.
    full_name: str | None = Field(default=None, max_length=255)
