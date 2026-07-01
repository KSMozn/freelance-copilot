"""DailyReportService — aggregate the last 24h + email admins.

Called from `POST /admin/tasks/daily-report`; that endpoint is fired by
Cloud Scheduler on a fixed cron. This module is deliberately pure with
respect to HTTP: build → render → send, and the endpoint is a thin
wrapper.

The aggregation reuses shapes already proven in `admin_service` —
signup / login counts, funnel derivation — with a `created_at` window
bound added. Nothing here is expensive against the current data size;
if the tables grow we can move to a materialized view later.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.admin_dto import DailyReportResult
from app.core.config import get_settings
from app.domain.providers.email_provider import EmailMessage, EmailProvider
from app.infrastructure.db.models.admin_user import AdminUser
from app.infrastructure.db.models.feedback_entry import FeedbackEntry
from app.infrastructure.db.models.student_profile import StudentProfile
from app.infrastructure.db.models.usage_event import UsageEvent
from app.infrastructure.db.models.user import User
from app.infrastructure.email.template_renderer import render

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TemplateCount:
    template: str
    count: int


@dataclass(slots=True)
class FeedbackLine:
    email: str
    kind: str
    rating: int | None
    template_slug: str | None
    message: str | None
    created_at: datetime


@dataclass(slots=True)
class DailyReport:
    window_start: datetime
    window_end: datetime
    signups_today: int
    logins_today: int
    downloads_today: int
    downloads_today_by_template: list[TemplateCount]
    most_used_template_all_time: str | None
    started_no_download: int
    total_users: int
    general_feedback: list[FeedbackLine] = field(default_factory=list)
    surveys: list[FeedbackLine] = field(default_factory=list)


class DailyReportService:
    def __init__(
        self, session: AsyncSession, email_provider: EmailProvider
    ) -> None:
        self._session = session
        self._email = email_provider

    # ---- Aggregation ------------------------------------------------

    async def build_report(
        self, *, window_hours: int = 24
    ) -> DailyReport:
        window_end = datetime.now(UTC)
        window_start = window_end - timedelta(hours=window_hours)

        total_users = await self._scalar(select(func.count(User.id)))

        signups_today = await self._scalar(
            select(func.count(User.id)).where(User.created_at >= window_start)
        )
        logins_today = await self._scalar(
            select(func.count(User.id)).where(
                User.last_login_at.is_not(None),
                User.last_login_at >= window_start,
            )
        )

        # Downloads in-window, grouped by template. The templated
        # meta.template field went in with phase L; older rows may be
        # missing it — those bucket under 'unknown'.
        template_col = UsageEvent.meta["template"].astext.label("template")
        dl_rows = (
            await self._session.execute(
                select(template_col, func.count(UsageEvent.id))
                .where(
                    UsageEvent.kind == "cv.pdf",
                    UsageEvent.status == "ok",
                    UsageEvent.created_at >= window_start,
                )
                .group_by(template_col)
                .order_by(func.count(UsageEvent.id).desc())
            )
        ).all()
        downloads_today_by_template = [
            TemplateCount(template=(t or "unknown"), count=c)
            for (t, c) in dl_rows
        ]
        downloads_today = sum(c.count for c in downloads_today_by_template)

        # Most-used template all-time.
        alltime = (
            await self._session.execute(
                select(template_col, func.count(UsageEvent.id))
                .where(
                    UsageEvent.kind == "cv.pdf",
                    UsageEvent.status == "ok",
                )
                .group_by(template_col)
                .order_by(func.count(UsageEvent.id).desc())
                .limit(1)
            )
        ).first()
        most_used_template_all_time = (
            (alltime[0] or "unknown") if alltime else None
        )

        # Wizard leakage — completed at least one step but never
        # downloaded a CV (all time, not window-bound; matches the
        # spirit of "if anyone started without downloading the CV").
        started_ids = (
            await self._session.execute(
                select(StudentProfile.user_id).where(
                    func.jsonb_array_length(StudentProfile.completed_steps) > 0
                )
            )
        ).all()
        downloader_ids = (
            await self._session.execute(
                select(func.distinct(UsageEvent.user_id)).where(
                    UsageEvent.kind == "cv.pdf",
                    UsageEvent.status == "ok",
                )
            )
        ).all()
        downloaders = {uid for (uid,) in downloader_ids if uid is not None}
        started_no_download = sum(
            1 for (uid,) in started_ids if uid not in downloaders
        )

        # Feedback + surveys in-window.
        fb_rows = (
            await self._session.execute(
                select(FeedbackEntry, User.email)
                .join(User, User.id == FeedbackEntry.user_id)
                .where(FeedbackEntry.created_at >= window_start)
                .order_by(FeedbackEntry.created_at.desc())
            )
        ).all()
        general: list[FeedbackLine] = []
        surveys: list[FeedbackLine] = []
        for row, email in fb_rows:
            line = FeedbackLine(
                email=email,
                kind=row.kind,
                rating=row.rating,
                template_slug=row.template_slug,
                message=row.message,
                created_at=row.created_at,
            )
            if row.kind == "general":
                general.append(line)
            else:
                surveys.append(line)

        return DailyReport(
            window_start=window_start,
            window_end=window_end,
            signups_today=signups_today,
            logins_today=logins_today,
            downloads_today=downloads_today,
            downloads_today_by_template=downloads_today_by_template,
            most_used_template_all_time=most_used_template_all_time,
            started_no_download=started_no_download,
            total_users=total_users,
            general_feedback=general,
            surveys=surveys,
        )

    # ---- Delivery ----------------------------------------------------

    async def send(self, report: DailyReport) -> DailyReportResult:
        recipients = [
            e
            for (e,) in (
                await self._session.execute(
                    select(AdminUser.email).where(AdminUser.is_active.is_(True))
                )
            ).all()
        ]
        if not recipients:
            return DailyReportResult(recipients=0, delivered=0, errors=[])

        html_body, text_body = self._render_bodies(report)
        s = get_settings()
        subject = (
            f"[{s.app_name}] Daily report — "
            f"{report.window_start.date().isoformat()}"
        )

        delivered = 0
        errors: list[str] = []
        for to in recipients:
            try:
                await self._email.send(
                    EmailMessage(
                        to=to,
                        subject=subject,
                        html_body=html_body,
                        text_body=text_body,
                        tags={"kind": "daily_report"},
                    )
                )
                delivered += 1
            except Exception as exc:  # noqa: BLE001 — capture per-recipient
                errors.append(f"{to}: {exc}")
                logger.exception("Daily report delivery failed for %s", to)

        return DailyReportResult(
            recipients=len(recipients),
            delivered=delivered,
            errors=errors,
        )

    def _render_bodies(self, r: DailyReport) -> tuple[str, str]:
        # Templates that need loops (feedback + surveys + template
        # counts) get their variable-length sections pre-rendered here
        # as HTML / text blocks and injected via a single placeholder.
        # Keeps the shared `str.format_map` renderer.
        by_template_html = "".join(
            f"<tr><td>{_esc(tc.template)}</td>"
            f"<td style='text-align:right'>{tc.count}</td></tr>"
            for tc in r.downloads_today_by_template
        ) or "<tr><td colspan='2' style='color:#6b7280'>None today</td></tr>"
        by_template_txt = "\n".join(
            f"  {tc.template}: {tc.count}"
            for tc in r.downloads_today_by_template
        ) or "  (none today)"

        general_html = "".join(
            f"<li><strong>{_esc(f.email)}</strong> "
            f"<span style='color:#6b7280'>({f.created_at.strftime('%H:%M UTC')})</span>"
            f"<div style='margin-top:4px;white-space:pre-wrap'>{_esc(f.message or '')}</div></li>"
            for f in r.general_feedback
        ) or "<li style='color:#6b7280'>None in this window.</li>"
        general_txt = "\n\n".join(
            f"- {f.email} ({f.created_at.strftime('%H:%M UTC')}):\n{f.message or ''}"
            for f in r.general_feedback
        ) or "  (none in this window)"

        surveys_html = "".join(
            f"<li>{'★' * (f.rating or 0)}{'☆' * (5 - (f.rating or 0))} · "
            f"<strong>{_esc(f.template_slug or 'unknown')}</strong> "
            f"<span style='color:#6b7280'>· {_esc(f.email)}</span>"
            + (
                f"<div style='margin-top:4px;white-space:pre-wrap'>{_esc(f.message)}</div>"
                if f.message
                else ""
            )
            + "</li>"
            for f in r.surveys
        ) or "<li style='color:#6b7280'>None in this window.</li>"
        surveys_txt = "\n".join(
            f"  {f.rating}/5 stars · {f.template_slug or 'unknown'} · {f.email}"
            + (f"\n    {f.message}" if f.message else "")
            for f in r.surveys
        ) or "  (none in this window)"

        s = get_settings()
        context = {
            "app_name": s.app_name,
            "window_start": r.window_start.strftime("%Y-%m-%d %H:%M UTC"),
            "window_end": r.window_end.strftime("%Y-%m-%d %H:%M UTC"),
            "total_users": r.total_users,
            "signups_today": r.signups_today,
            "logins_today": r.logins_today,
            "downloads_today": r.downloads_today,
            "most_used_template_all_time": r.most_used_template_all_time
            or "—",
            "started_no_download": r.started_no_download,
            "by_template_rows_html": by_template_html,
            "by_template_rows_txt": by_template_txt,
            "general_feedback_html": general_html,
            "general_feedback_txt": general_txt,
            "surveys_html": surveys_html,
            "surveys_txt": surveys_txt,
            "admin_url": s.admin_base_url,
        }
        return render("daily_report.html", context), render(
            "daily_report.txt", context
        )

    async def _scalar(self, stmt) -> int:  # type: ignore[no-untyped-def]
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)


def _esc(v: object) -> str:
    """Minimal HTML escape for user-supplied text in the email body."""
    s = str(v)
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
