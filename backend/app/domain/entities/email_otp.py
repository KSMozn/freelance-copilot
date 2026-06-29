from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

OtpPurpose = Literal["login", "register", "email_change"]


@dataclass(slots=True)
class EmailOtp:
    id: UUID
    email: str
    code_hash: str
    purpose: OtpPurpose
    expires_at: datetime
    consumed_at: datetime | None
    attempts: int
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
