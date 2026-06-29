from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.skill_catalog import SkillCatalogEntry, SkillCategory
from app.infrastructure.db.models.skill_catalog import SkillCatalog


def _to_domain(row: SkillCatalog) -> SkillCatalogEntry:
    return SkillCatalogEntry(
        id=row.id,
        slug=row.slug,
        name=row.name,
        category=row.category,  # type: ignore[arg-type]
        aliases=list(row.aliases or []),
        is_system_seeded=row.is_system_seeded,
        created_by_user_id=row.created_by_user_id,
        created_at=row.created_at,
    )


class SQLAlchemySkillCatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, skill_id: UUID) -> SkillCatalogEntry | None:
        row = await self._session.get(SkillCatalog, skill_id)
        return _to_domain(row) if row else None

    async def get_by_slug(self, slug: str) -> SkillCatalogEntry | None:
        stmt = select(SkillCatalog).where(SkillCatalog.slug == slug)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def find_by_alias(self, alias_slug: str) -> SkillCatalogEntry | None:
        # JSONB containment: `aliases @> '["foo"]'`
        result = await self._session.execute(
            text(
                "SELECT * FROM skill_catalog "
                "WHERE aliases @> CAST(:needle AS jsonb) LIMIT 1"
            ).bindparams(needle=f'["{alias_slug}"]'),
        )
        mapped = result.mappings().first()
        if not mapped:
            return None
        return _to_domain_dict(dict(mapped))

    async def find_by_fuzzy_name(
        self, name: str, threshold: float = 0.85
    ) -> SkillCatalogEntry | None:
        result = await self._session.execute(
            text(
                """
                SELECT * FROM skill_catalog
                WHERE similarity(name, :name) >= :threshold
                ORDER BY similarity(name, :name) DESC
                LIMIT 1
                """
            ).bindparams(name=name, threshold=threshold),
        )
        mapped = result.mappings().first()
        if not mapped:
            return None
        return _to_domain_dict(dict(mapped))

    async def create(
        self,
        *,
        slug: str,
        name: str,
        category: SkillCategory,
        aliases: list[str] | None = None,
        is_system_seeded: bool = False,
        created_by_user_id: UUID | None = None,
    ) -> SkillCatalogEntry:
        row = SkillCatalog(
            slug=slug,
            name=name,
            category=category,
            aliases=list(aliases or []),
            is_system_seeded=is_system_seeded,
            created_by_user_id=created_by_user_id,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _to_domain(row)

    async def list_all(self) -> list[SkillCatalogEntry]:
        stmt = select(SkillCatalog).order_by(SkillCatalog.category, SkillCatalog.name)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_domain(r) for r in rows]


def _to_domain_dict(row: dict) -> SkillCatalogEntry:
    return SkillCatalogEntry(
        id=row["id"],
        slug=row["slug"],
        name=row["name"],
        category=row["category"],
        aliases=list(row.get("aliases") or []),
        is_system_seeded=row["is_system_seeded"],
        created_by_user_id=row.get("created_by_user_id"),
        created_at=row.get("created_at"),
    )
