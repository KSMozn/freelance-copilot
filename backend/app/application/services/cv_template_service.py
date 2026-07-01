"""CvTemplateService — CV template registry queries + admin toggles.

Bridges the DB-backed metadata table `cv_templates` (visibility, sort
order, display name) and the filesystem template registry that lives on
`StudentCvRenderer`. Resolves the effective template slug for a render
request via the chain: caller override → student's saved default →
first visible → hard fallback to `classic`.

Admin mutations audit through `usage_event_service.fire` following the
same `admin.action` pattern used elsewhere in the admin routes.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.student_cv_renderer import StudentCvRenderer
from app.infrastructure.db.models.cv_template import CvTemplate

# Hard fallback if the DB is empty and the filesystem registry somehow
# lacks a match. Should never happen post-migration but keeps rendering
# from throwing on a fresh dev DB before seeds run.
_HARD_FALLBACK_SLUG = "classic"


class CvTemplateService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[CvTemplate]:
        rows = await self._session.execute(
            select(CvTemplate).order_by(
                CvTemplate.sort_order.asc(), CvTemplate.slug.asc()
            )
        )
        return list(rows.scalars().all())

    async def list_visible(self) -> list[CvTemplate]:
        rows = await self._session.execute(
            select(CvTemplate)
            .where(CvTemplate.is_visible.is_(True))
            .order_by(CvTemplate.sort_order.asc(), CvTemplate.slug.asc())
        )
        return list(rows.scalars().all())

    async def get(self, slug: str) -> CvTemplate | None:
        return await self._session.get(CvTemplate, slug)

    async def resolve_slug(
        self, *, requested: str | None, profile_slug: str | None
    ) -> str:
        """Pick the actual slug to render.

        Order: `requested` (if visible) → `profile_slug` (if visible) →
        first visible row → `_HARD_FALLBACK_SLUG`. Any slug not backed by
        a filesystem template is dropped from consideration.
        """
        known = StudentCvRenderer.list_template_slugs()
        visible = await self.list_visible()
        visible_slugs = {t.slug for t in visible if t.slug in known}

        if requested and requested in visible_slugs:
            return requested
        if profile_slug and profile_slug in visible_slugs:
            return profile_slug
        if visible:
            for t in visible:
                if t.slug in known:
                    return t.slug
        return _HARD_FALLBACK_SLUG

    async def set_visibility(self, slug: str, *, visible: bool) -> CvTemplate | None:
        row = await self.get(slug)
        if row is None:
            return None
        row.is_visible = visible
        await self._session.flush()
        return row

    async def set_sort_order(self, slug: str, *, order: int) -> CvTemplate | None:
        row = await self.get(slug)
        if row is None:
            return None
        row.sort_order = order
        await self._session.flush()
        return row

    async def update(
        self,
        slug: str,
        *,
        is_visible: bool | None = None,
        sort_order: int | None = None,
    ) -> CvTemplate | None:
        row = await self.get(slug)
        if row is None:
            return None
        if is_visible is not None:
            row.is_visible = is_visible
        if sort_order is not None:
            row.sort_order = sort_order
        await self._session.flush()
        return row
