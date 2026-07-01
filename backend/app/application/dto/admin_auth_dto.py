from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class AdminTokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AdminUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime


class AdminAuthResponse(BaseModel):
    user: AdminUserRead
    tokens: AdminTokenPair


class AdminRefreshRequest(BaseModel):
    refresh_token: str
