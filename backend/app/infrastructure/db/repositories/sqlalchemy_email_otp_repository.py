from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.email_otp import EmailOtp, OtpPurpose
from app.infrastructure.db.models.email_otp_code import EmailOtpCode


def _to_domain(row: EmailOtpCode) -> EmailOtp:
    return EmailOtp(
        id=row.id,
        email=row.email,
        code_hash=row.code_hash,
        purpose=row.purpose,  # type: ignore[arg-type]
        expires_at=row.expires_at,
        consumed_at=row.consumed_at,
        attempts=row.attempts,
        ip_address=row.ip_address,
        user_agent=row.user_agent,
        created_at=row.created_at,
    )


class SQLAlchemyEmailOtpRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        email: str,
        code_hash: str,
        purpose: OtpPurpose,
        expires_at: datetime,
        ip_address: str | None,
        user_agent: str | None,
    ) -> EmailOtp:
        row = EmailOtpCode(
            email=email,
            code_hash=code_hash,
            purpose=purpose,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _to_domain(row)

    async def count_recent_issues(
        self, *, email: str, purpose: OtpPurpose, since: datetime
    ) -> int:
        stmt = (
            select(func.count(EmailOtpCode.id))
            .where(EmailOtpCode.email == email)
            .where(EmailOtpCode.purpose == purpose)
            .where(EmailOtpCode.created_at >= since)
        )
        return int((await self._session.execute(stmt)).scalar_one() or 0)

    async def delete(self, otp_id: UUID) -> None:
        row = await self._session.get(EmailOtpCode, otp_id)
        if row is not None:
            await self._session.delete(row)
            await self._session.commit()

    async def get_active(
        self, *, email: str, purpose: OtpPurpose
    ) -> EmailOtp | None:
        # Always return the newest code, even if consumed. Otherwise consuming
        # it would make an older unconsumed code active again.
        stmt = (
            select(EmailOtpCode)
            .where(EmailOtpCode.email == email)
            .where(EmailOtpCode.purpose == purpose)
            .order_by(EmailOtpCode.created_at.desc())
            .limit(1)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def increment_attempts(self, otp_id: UUID) -> None:
        await self._session.execute(
            update(EmailOtpCode)
            .where(EmailOtpCode.id == otp_id)
            .where(EmailOtpCode.consumed_at.is_(None))
            .values(attempts=EmailOtpCode.attempts + 1)
        )
        await self._session.commit()

    async def mark_consumed(self, otp_id: UUID, consumed_at: datetime) -> bool:
        result = await self._session.execute(
            update(EmailOtpCode)
            .where(EmailOtpCode.id == otp_id)
            .where(EmailOtpCode.consumed_at.is_(None))
            .values(consumed_at=consumed_at)
            .returning(EmailOtpCode.id)
        )
        await self._session.commit()
        return result.scalar_one_or_none() is not None
