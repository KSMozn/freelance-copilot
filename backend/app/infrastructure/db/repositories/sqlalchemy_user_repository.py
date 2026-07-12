from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User as DomainUser
from app.infrastructure.db.models.user import User as UserModel


def _to_domain(row: UserModel) -> DomainUser:
    return DomainUser(
        id=row.id,
        email=row.email,
        password_hash=row.password_hash,
        full_name=row.full_name,
        is_active=row.is_active,
        is_superuser=row.is_superuser,
        created_at=row.created_at,
        updated_at=row.updated_at,
        email_verified_at=row.email_verified_at,
        last_login_at=row.last_login_at,
        selected_persona_kind=row.selected_persona_kind,
    )


class SQLAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> DomainUser | None:
        row = await self._session.get(UserModel, user_id)
        return _to_domain(row) if row else None

    async def get_by_email(self, email: str) -> DomainUser | None:
        stmt = select(UserModel).where(UserModel.email == email)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def create(
        self,
        *,
        email: str,
        password_hash: str | None,
        full_name: str | None,
        email_verified_at: datetime | None = None,
        selected_persona_kind: str = "professional",
    ) -> DomainUser:
        row = UserModel(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            email_verified_at=email_verified_at,
            selected_persona_kind=selected_persona_kind,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _to_domain(row)

    async def set_persona_kind(self, user_id: UUID, kind: str) -> None:
        row = await self._session.get(UserModel, user_id)
        if row is None:
            return
        row.selected_persona_kind = kind
        await self._session.commit()

    async def set_password(self, user_id: UUID, password_hash: str) -> None:
        row = await self._session.get(UserModel, user_id)
        if row is None:
            return
        row.password_hash = password_hash
        await self._session.commit()

    async def mark_email_verified(
        self, user_id: UUID, verified_at: datetime
    ) -> None:
        row = await self._session.get(UserModel, user_id)
        if row is None:
            return
        if row.email_verified_at is None:
            row.email_verified_at = verified_at
            await self._session.commit()

    async def touch_last_login(self, user_id: UUID, at: datetime) -> None:
        row = await self._session.get(UserModel, user_id)
        if row is None:
            return
        row.last_login_at = at
        await self._session.commit()
