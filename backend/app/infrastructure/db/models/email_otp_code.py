from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import CITEXT, INET
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base

OTP_PURPOSES = ("login", "register", "email_change")


class EmailOtpCode(Base):
    __tablename__ = "email_otp_codes"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(CITEXT(), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(
        Enum(*OTP_PURPOSES, name="otp_purpose"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
