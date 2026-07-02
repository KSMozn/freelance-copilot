"""Tests for the DailyReport body renderer.

DB-side aggregation is exercised end-to-end by the admin endpoint test
(would need a real Postgres, deferred to the live smoke). This file
pins the string-substitution behavior: escaping, plural-safe fallbacks
when the window is empty, and star glyph rendering.
"""
from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-please-change-me-32b")

from datetime import UTC, datetime

from app.application.services.daily_report_service import (
    DailyReport,
    DailyReportService,
    FeedbackLine,
    TemplateCount,
)


def _report(**overrides) -> DailyReport:  # type: ignore[no-untyped-def]
    base = {
        "window_start": datetime(2026, 7, 1, 0, 0, tzinfo=UTC),
        "window_end": datetime(2026, 7, 2, 0, 0, tzinfo=UTC),
        "signups_today": 0,
        "logins_today": 0,
        "downloads_today": 0,
        "downloads_today_by_template": [],
        "most_used_template_all_time": None,
        "started_no_download": 0,
        "total_users": 0,
        "general_feedback": [],
        "surveys": [],
    }
    base.update(overrides)
    return DailyReport(**base)


def _svc() -> DailyReportService:
    return DailyReportService.__new__(DailyReportService)


def test_empty_window_renders_none_placeholders() -> None:
    html, txt = _svc()._render_bodies(_report())
    assert "None today" in html
    assert "(none today)" in txt
    assert "None in this window." in html
    assert "(none in this window)" in txt


def test_stats_land_in_both_bodies() -> None:
    html, txt = _svc()._render_bodies(
        _report(signups_today=3, logins_today=7, downloads_today=5, total_users=42)
    )
    assert ">3<" in html and ">7<" in html and ">5<" in html and ">42<" in html
    assert "Signups today:        3" in txt
    assert "Logins today:         7" in txt
    assert "Downloads today:      5" in txt


def test_template_rows_ordered_as_given() -> None:
    html, txt = _svc()._render_bodies(
        _report(
            downloads_today=5,
            downloads_today_by_template=[
                TemplateCount("classic", 3),
                TemplateCount("modern", 2),
            ],
        )
    )
    assert html.index("classic") < html.index("modern")
    assert "classic: 3" in txt
    assert "modern: 2" in txt


def test_surveys_render_stars() -> None:
    html, txt = _svc()._render_bodies(
        _report(
            surveys=[
                FeedbackLine(
                    email="s@x.com",
                    kind="post_download",
                    rating=4,
                    template_slug="minimal",
                    message="great",
                    created_at=datetime(2026, 7, 1, 11, 0, tzinfo=UTC),
                )
            ]
        )
    )
    assert "★★★★☆" in html  # 4-star row
    assert "4/5 stars · minimal · s@x.com" in txt
    assert "great" in html and "great" in txt


def test_user_supplied_html_is_escaped() -> None:
    html, _ = _svc()._render_bodies(
        _report(
            general_feedback=[
                FeedbackLine(
                    email="x@y.com",
                    kind="general",
                    rating=None,
                    template_slug=None,
                    message="<script>evil()</script>",
                    created_at=datetime(2026, 7, 1, 8, 0, tzinfo=UTC),
                )
            ]
        )
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_leakage_line_appears() -> None:
    _, txt = _svc()._render_bodies(_report(started_no_download=4))
    assert "4 student(s) started the wizard but never downloaded a CV." in txt


def test_missing_template_falls_back_to_dash() -> None:
    _, txt = _svc()._render_bodies(_report(most_used_template_all_time=None))
    assert "Most-used template all-time: —" in txt
