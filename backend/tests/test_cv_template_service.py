"""Tests for CvTemplateService.

We fake the AsyncSession because the service's queries are shallow and
the test suite convention is to avoid a real Postgres for unit-scoped
work. The stub only implements the methods CvTemplateService touches
(`execute`, `get`, `flush`) and returns pre-seeded lists.
"""
from __future__ import annotations

from datetime import UTC, datetime

from app.application.services.cv_template_service import CvTemplateService
from app.infrastructure.db.models.cv_template import CvTemplate


def _tmpl(slug: str, *, visible: bool = True, order: int = 100) -> CvTemplate:
    row = CvTemplate()
    row.slug = slug
    row.display_name = slug.capitalize()
    row.description = f"{slug} template"
    row.is_visible = visible
    row.sort_order = order
    row.created_at = datetime.now(UTC)
    row.updated_at = datetime.now(UTC)
    return row


class _FakeScalarResult:
    def __init__(self, rows: list[CvTemplate]) -> None:
        self._rows = rows

    def scalars(self) -> _FakeScalarResult:
        return self

    def all(self) -> list[CvTemplate]:
        return list(self._rows)


class _FakeSession:
    """Minimal AsyncSession stub tailored to CvTemplateService.

    The service issues two shapes of query: `execute(select(...))` for
    lists and `session.get(model, pk)` for by-slug lookup. The stub
    inspects the compiled SQL string to decide whether to filter to
    visible-only.
    """

    def __init__(self, rows: list[CvTemplate]) -> None:
        self._rows = rows
        self.flushed = False

    async def execute(self, stmt):  # type: ignore[no-untyped-def]
        # `list_visible()` adds a WHERE clause; `list_all()` doesn't.
        # Introspect the SQLAlchemy Select's WHERE criteria instead of
        # scanning the compiled SQL (which projects `is_visible` in the
        # SELECT list either way).
        rows = sorted(self._rows, key=lambda r: (r.sort_order, r.slug))
        has_where = getattr(stmt, "whereclause", None) is not None
        if has_where:
            rows = [r for r in rows if r.is_visible]
        return _FakeScalarResult(rows)

    async def get(self, _model, slug: str) -> CvTemplate | None:
        for r in self._rows:
            if r.slug == slug:
                return r
        return None

    async def flush(self) -> None:
        self.flushed = True


async def test_list_all_returns_sorted_including_hidden() -> None:
    session = _FakeSession(
        [
            _tmpl("modern", visible=True, order=20),
            _tmpl("classic", visible=True, order=10),
            _tmpl("hidden", visible=False, order=5),
        ]
    )
    svc = CvTemplateService(session)  # type: ignore[arg-type]
    all_rows = await svc.list_all()
    assert [r.slug for r in all_rows] == ["hidden", "classic", "modern"]


async def test_list_visible_filters_and_sorts() -> None:
    session = _FakeSession(
        [
            _tmpl("modern", visible=True, order=20),
            _tmpl("classic", visible=True, order=10),
            _tmpl("hidden", visible=False, order=5),
        ]
    )
    svc = CvTemplateService(session)  # type: ignore[arg-type]
    visible = await svc.list_visible()
    assert [r.slug for r in visible] == ["classic", "modern"]


async def test_resolve_slug_prefers_requested_when_visible() -> None:
    session = _FakeSession(
        [
            _tmpl("classic", visible=True, order=10),
            _tmpl("modern", visible=True, order=20),
        ]
    )
    svc = CvTemplateService(session)  # type: ignore[arg-type]
    slug = await svc.resolve_slug(requested="modern", profile_slug="classic")
    assert slug == "modern"


async def test_resolve_slug_falls_back_to_profile_when_requested_hidden() -> None:
    session = _FakeSession(
        [
            _tmpl("classic", visible=True, order=10),
            _tmpl("modern", visible=False, order=20),  # hidden by admin
        ]
    )
    svc = CvTemplateService(session)  # type: ignore[arg-type]
    slug = await svc.resolve_slug(requested="modern", profile_slug="classic")
    assert slug == "classic"


async def test_resolve_slug_falls_back_to_first_visible_when_profile_hidden() -> None:
    session = _FakeSession(
        [
            _tmpl("classic", visible=True, order=10),
            _tmpl("modern", visible=False, order=20),
        ]
    )
    svc = CvTemplateService(session)  # type: ignore[arg-type]
    slug = await svc.resolve_slug(requested=None, profile_slug="modern")
    assert slug == "classic"


async def test_resolve_slug_hard_fallback_when_no_visible() -> None:
    session = _FakeSession(
        [
            _tmpl("modern", visible=False, order=20),
        ]
    )
    svc = CvTemplateService(session)  # type: ignore[arg-type]
    slug = await svc.resolve_slug(requested=None, profile_slug=None)
    assert slug == "classic"  # hard fallback, even if not in DB


async def test_resolve_slug_ignores_unknown_filesystem_slug() -> None:
    # DB has a template row but the filesystem registry doesn't back it —
    # resolver must skip it.
    session = _FakeSession(
        [
            _tmpl("phantom-template-not-on-disk", visible=True, order=10),
            _tmpl("classic", visible=True, order=20),
        ]
    )
    svc = CvTemplateService(session)  # type: ignore[arg-type]
    slug = await svc.resolve_slug(
        requested="phantom-template-not-on-disk", profile_slug=None
    )
    assert slug == "classic"


async def test_update_flushes_and_returns_row() -> None:
    session = _FakeSession(
        [
            _tmpl("classic", visible=True, order=10),
        ]
    )
    svc = CvTemplateService(session)  # type: ignore[arg-type]
    row = await svc.update("classic", is_visible=False, sort_order=99)
    assert row is not None
    assert row.is_visible is False
    assert row.sort_order == 99
    assert session.flushed


async def test_update_returns_none_for_unknown_slug() -> None:
    session = _FakeSession([_tmpl("classic")])
    svc = CvTemplateService(session)  # type: ignore[arg-type]
    row = await svc.update("nonexistent", is_visible=False)
    assert row is None
