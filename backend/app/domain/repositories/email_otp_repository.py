from datetime import datetime
from typing import Protocol

from app.domain.entities.email_otp import EmailOtp, OtpPurpose


class EmailOtpRepository(Protocol):
    async def create(
        self,
        *,
        email: str,
        code_hash: str,
        purpose: OtpPurpose,
        expires_at: datetime,
        ip_address: str | None,
        user_agent: str | None,
    ) -> EmailOtp: ...

    async def count_recent_issues(
        self, *, email: str, purpose: OtpPurpose, since: datetime
    ) -> int: ...

    async def get_active(
        self, *, email: str, purpose: OtpPurpose
    ) -> EmailOtp | None: ...

    async def increment_attempts(self, otp_id) -> None: ...

    async def mark_consumed(self, otp_id, consumed_at: datetime) -> None: ...
