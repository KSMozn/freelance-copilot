from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.admin_user import AdminUser as DomainAdmin
from app.infrastructure.db.models.admin_user import AdminUser as AdminModel


def _to_domain(row: AdminModel) -> DomainAdmin:
    return DomainAdmin(
        id=row.id,
        email=row.email,
        password_hash=row.password_hash,
        full_name=row.full_name,
        is_active=row.is_active,
        last_login_at=row.last_login_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SQLAlchemyAdminUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, admin_id: UUID) -> DomainAdmin | None:
        row = await self._session.get(AdminModel, admin_id)
        return _to_domain(row) if row else None

    async def get_by_email(self, email: str) -> DomainAdmin | None:
        stmt = select(AdminModel).where(AdminModel.email == email)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def create(
        self,
        *,
        email: str,
        password_hash: str,
        full_name: str | None,
    ) -> DomainAdmin:
        row = AdminModel(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _to_domain(row)

    async def touch_last_login(self, admin_id: UUID, at: datetime) -> None:
        row = await self._session.get(AdminModel, admin_id)
        if row is None:
            return
        row.last_login_at = at
        await self._session.commit()
