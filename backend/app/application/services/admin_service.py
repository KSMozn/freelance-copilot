"""AdminService — all aggregations, lookups and mutations for /admin/*.

Lives close to SQLAlchemy because every method is a query — pushing this
behind a repository layer would just add ceremony. Read-heavy: overview,
users list, user detail, activity list. Mutations are narrow: toggle
is_active, reset wizard progress, hard delete, mint impersonation
tokens. Each mutation records a `usage_event` row so the actions have
an audit trail.
"""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import Integer, Numeric, case, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.admin_dto import (
    AdminActivityRow,
    AdminEntryDetail,
    AdminOverview,
    AdminStudentSummary,
    AdminUserDetail,
    AdminUserRow,
    BulkRecipient,
    EmailPreviewResponse,
    EntryKindCount,
    LlmSpendByModel,
    LlmSpendSummary,
    SignupsPoint,
    UsageKindCount,
    WizardFunnel,
)
from app.application.email_templates import EmailTemplateSpec, get_template
from app.core.config import Settings
from app.domain.providers.email_provider import EmailMessage
from app.infrastructure.db.models.student_profile import (
    StudentProfile,
    StudentProfileEntry,
)
from app.infrastructure.db.models.usage_event import UsageEvent
from app.infrastructure.db.models.user import User
from app.infrastructure.email.template_renderer import render

WIZARD_STEPS = (
    "basics",
    "education",
    "photo",
    "skills",
    "courses",
    "projects",
    "internships",
    "volunteer",
    "languages",
    "certificates",
    "summary",
    "preview",
    "starter-pack",
)


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---- Overview -----------------------------------------------------

    async def get_overview(self) -> AdminOverview:
        now = datetime.now(UTC)
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago_date = today - timedelta(days=29)  # 30-day window inclusive

        users_total = await self._scalar(select(func.count(User.id)))
        users_students = await self._scalar(
            select(func.count(User.id)).where(
                User.selected_persona_kind == "student"
            )
        )
        users_active_7d = await self._scalar(
            select(func.count(User.id)).where(User.last_login_at >= week_ago)
        )
        signups_today = await self._scalar(
            select(func.count(User.id)).where(
                func.date(User.created_at) == today
            )
        )
        signups_7d = await self._scalar(
            select(func.count(User.id)).where(User.created_at >= week_ago)
        )
        signups_30d = await self._scalar(
            select(func.count(User.id)).where(
                func.date(User.created_at) >= month_ago_date
            )
        )

        # Signups per day for the last 30 days — fill zero-days on the
        # Python side so the chart doesn't skip empty days.
        rows = (
            await self._session.execute(
                select(
                    func.date(User.created_at).label("d"),
                    func.count(User.id).label("c"),
                )
                .where(func.date(User.created_at) >= month_ago_date)
                .group_by("d")
            )
        ).all()
        counts_by_day: dict[date, int] = {r.d: r.c for r in rows}
        signups_series: list[SignupsPoint] = []
        for offset in range(30):
            d = month_ago_date + timedelta(days=offset)
            signups_series.append(SignupsPoint(day=d, count=counts_by_day.get(d, 0)))

        funnel = await self._compute_funnel(users_total)

        # Entries by kind
        entry_rows = (
            await self._session.execute(
                select(
                    StudentProfileEntry.kind,
                    func.count(StudentProfileEntry.id),
                ).group_by(StudentProfileEntry.kind)
            )
        ).all()
        entries_by_kind = [
            EntryKindCount(kind=k, count=c) for (k, c) in entry_rows
        ]

        # Usage counts over the last 7d
        usage_rows = (
            await self._session.execute(
                select(
                    UsageEvent.kind,
                    func.count(UsageEvent.id).label("total"),
                    func.sum(case((UsageEvent.status == "error", 1), else_=0)).label(
                        "errors"
                    ),
                )
                .where(UsageEvent.created_at >= week_ago)
                .group_by(UsageEvent.kind)
                .order_by(func.count(UsageEvent.id).desc())
            )
        ).all()
        usage_by_kind_7d = [
            UsageKindCount(kind=k, count=int(t or 0), errors=int(e or 0))
            for (k, t, e) in usage_rows
        ]

        # LLM spend rolls over 30 days (was 7d); at current volume 7d is
        # noisy — half a week of low usage looks like the coach is broken.
        # 30d is stable enough to spot trends without being stale.
        llm_since = now - timedelta(days=30)
        llm_spend_30d = await self._compute_llm_spend(llm_since)

        return AdminOverview(
            users_total=users_total,
            users_students=users_students,
            users_active_7d=users_active_7d,
            signups_today=signups_today,
            signups_7d=signups_7d,
            signups_30d=signups_30d,
            signups_series=signups_series,
            funnel=funnel,
            entries_by_kind=entries_by_kind,
            usage_by_kind_7d=usage_by_kind_7d,
            llm_spend_30d=llm_spend_30d,
        )

    async def compute_user_llm_spend(
        self, user_id: UUID, *, since_days: int = 30
    ) -> LlmSpendSummary:
        """Public wrapper — user-scoped LLM spend for the admin user page."""
        since = datetime.now(tz=UTC) - timedelta(days=since_days)
        return await self._compute_llm_spend(since, user_id=user_id)

    async def _compute_llm_spend(
        self,
        since: datetime,
        *,
        user_id: UUID | None = None,
    ) -> LlmSpendSummary:
        """Aggregate token usage + estimated USD cost from usage_events.

        Only events that carry `meta.prompt_tokens` count — legacy or
        non-LLM rows are ignored. Numeric fields inside JSONB come back
        as strings from Postgres; we cast + fall back to 0 on missing
        keys so the query never blows up on a partially-populated row.

        Uses a subquery to materialize the JSONB-extraction expressions
        once — putting them directly in GROUP BY vs. SELECT produced two
        separate parameter placeholders under asyncpg + Postgres refused
        to recognize them as the same expression.

        Pass `user_id` to scope the aggregation to a single user (used
        by the per-user LLM spend card on the admin user-detail page).
        """
        inner_stmt = (
            select(
                func.coalesce(
                    UsageEvent.meta.op("->>")("model"), "unknown"
                ).label("model"),
                func.coalesce(
                    func.cast(
                        UsageEvent.meta.op("->>")("prompt_tokens"), Integer
                    ),
                    0,
                ).label("pt"),
                func.coalesce(
                    func.cast(
                        UsageEvent.meta.op("->>")("completion_tokens"), Integer
                    ),
                    0,
                ).label("ct"),
                func.coalesce(
                    func.cast(
                        UsageEvent.meta.op("->>")("cost_usd"), Numeric(12, 6)
                    ),
                    0,
                ).label("cost"),
            )
            .where(UsageEvent.created_at >= since)
            .where(UsageEvent.meta.op("?")("prompt_tokens"))
        )
        if user_id is not None:
            inner_stmt = inner_stmt.where(UsageEvent.user_id == user_id)
        inner = inner_stmt.subquery()
        stmt = (
            select(
                inner.c.model,
                func.count().label("calls"),
                func.sum(inner.c.pt).label("prompt_tokens"),
                func.sum(inner.c.ct).label("completion_tokens"),
                func.sum(inner.c.cost).label("cost_usd"),
            )
            .group_by(inner.c.model)
            .order_by(func.sum(inner.c.cost).desc())
        )
        rows = (await self._session.execute(stmt)).all()

        by_model = [
            LlmSpendByModel(
                model=str(m),
                calls=int(calls or 0),
                prompt_tokens=int(pt or 0),
                completion_tokens=int(ct or 0),
                cost_usd=float(cost or 0),
            )
            for (m, calls, pt, ct, cost) in rows
        ]
        return LlmSpendSummary(
            total_calls=sum(m.calls for m in by_model),
            total_prompt_tokens=sum(m.prompt_tokens for m in by_model),
            total_completion_tokens=sum(m.completion_tokens for m in by_model),
            total_cost_usd=round(sum(m.cost_usd for m in by_model), 4),
            by_model=by_model,
        )

    async def _compute_funnel(self, users_total: int) -> WizardFunnel:
        """Count students who reached each wizard step.

        Approach: read completed_steps JSONB and count occurrences per
        step. For "downloaded" we approximate via UsageEvent rows for
        cv.pdf. Cheaper than a series of queries; each list is small.
        """
        rows = (
            await self._session.execute(
                select(StudentProfile.completed_steps)
            )
        ).all()
        counts: dict[str, int] = {s: 0 for s in WIZARD_STEPS}
        for (steps,) in rows:
            if not steps:
                continue
            for step in steps:
                if step in counts:
                    counts[step] += 1

        # cv.pdf event counts = students who actually downloaded
        distinct_downloaders = await self._scalar(
            select(func.count(func.distinct(UsageEvent.user_id))).where(
                UsageEvent.kind == "cv.pdf", UsageEvent.status == "ok"
            )
        )

        return WizardFunnel(
            registered=users_total,
            basics=counts["basics"],
            education=counts["education"],
            photo=counts["photo"],
            skills=counts["skills"],
            courses=counts["courses"],
            projects=counts["projects"],
            internships=counts["internships"],
            volunteer=counts["volunteer"],
            languages=counts["languages"],
            certificates=counts["certificates"],
            summary=counts["summary"],
            preview=counts["preview"],
            starter_pack=counts["starter-pack"],
            downloaded=distinct_downloaders,
        )

    # ---- Users --------------------------------------------------------

    async def list_users(
        self,
        *,
        search: str | None,
        page: int,
        size: int,
        stuck_at: str | None = None,
        persona: str | None = None,
        active: bool | None = None,
        email_verified: bool | None = None,
        has_cv: bool | None = None,
        college: str | None = None,
        signed_up_after: datetime | None = None,
        signed_up_before: datetime | None = None,
    ) -> tuple[list[AdminUserRow], int]:
        """List users with optional filters — search / funnel cohort /
        persona / status / has-CV / college / signup date range.

        Filters compose (AND). `stuck_at` behavior is unchanged from
        item #6 (registered → no wizard progress, any wizard slug →
        stuck at that step). `has_cv=true` means the user has at least
        one successful `cv.pdf` event; `has_cv=false` means none.
        `college` matches by case-insensitive substring on
        `student_profiles.college`.
        """
        q = select(User)
        if search:
            like = f"%{search.strip().lower()}%"
            q = q.where(
                or_(
                    func.lower(User.email).like(like),
                    func.lower(func.coalesce(User.full_name, "")).like(like),
                )
            )
        if persona in ("student", "professional"):
            q = q.where(User.selected_persona_kind == persona)
        if active is True:
            q = q.where(User.is_active.is_(True))
        elif active is False:
            q = q.where(User.is_active.is_(False))
        if email_verified is True:
            q = q.where(User.email_verified_at.is_not(None))
        elif email_verified is False:
            q = q.where(User.email_verified_at.is_(None))
        if signed_up_after is not None:
            q = q.where(User.created_at >= signed_up_after)
        if signed_up_before is not None:
            q = q.where(User.created_at < signed_up_before)
        if college:
            college_like = f"%{college.strip().lower()}%"
            has_college = select(StudentProfile.user_id).where(
                StudentProfile.user_id == User.id,
                func.lower(func.coalesce(StudentProfile.college, "")).like(
                    college_like
                ),
            )
            q = q.where(has_college.exists())
        if has_cv is True:
            has_dl = select(UsageEvent.id).where(
                UsageEvent.user_id == User.id,
                UsageEvent.kind == "cv.pdf",
                UsageEvent.status == "ok",
            )
            q = q.where(has_dl.exists())
        elif has_cv is False:
            has_dl = select(UsageEvent.id).where(
                UsageEvent.user_id == User.id,
                UsageEvent.kind == "cv.pdf",
                UsageEvent.status == "ok",
            )
            q = q.where(~has_dl.exists())
        if stuck_at == "registered":
            # Everyone who has NOT completed the basics step yet: either
            # no student_profile row, or one with no completed_steps.
            no_progress = ~select(StudentProfile.user_id).where(
                StudentProfile.user_id == User.id,
                func.jsonb_array_length(StudentProfile.completed_steps) > 0,
            ).exists()
            q = q.where(no_progress)
        elif stuck_at in WIZARD_STEPS:
            idx = WIZARD_STEPS.index(stuck_at)
            next_slug = (
                WIZARD_STEPS[idx + 1] if idx + 1 < len(WIZARD_STEPS) else None
            )
            reached = select(StudentProfile.user_id).where(
                StudentProfile.user_id == User.id,
                StudentProfile.completed_steps.op("?")(stuck_at),
            )
            if next_slug is None:
                q = q.where(reached.exists())
            else:
                still_stuck = reached.where(
                    ~StudentProfile.completed_steps.op("?")(next_slug)
                )
                q = q.where(still_stuck.exists())
        # Total
        total = await self._scalar(
            select(func.count()).select_from(q.subquery())
        )
        # Page
        q = q.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size)
        users = (await self._session.execute(q)).scalars().all()

        # Batch-load profile wizard state for the returned page.
        ids = [u.id for u in users]
        profiles: dict[UUID, StudentProfile] = {}
        downloaded_ids: set[UUID] = set()
        if ids:
            prof_rows = (
                await self._session.execute(
                    select(StudentProfile).where(StudentProfile.user_id.in_(ids))
                )
            ).scalars().all()
            profiles = {p.user_id: p for p in prof_rows}
            # Distinct users on this page that have a successful cv.pdf event.
            dl_rows = (
                await self._session.execute(
                    select(func.distinct(UsageEvent.user_id))
                    .where(UsageEvent.user_id.in_(ids))
                    .where(UsageEvent.kind == "cv.pdf")
                    .where(UsageEvent.status == "ok")
                )
            ).scalars().all()
            downloaded_ids = {uid for uid in dl_rows if uid is not None}

        rows: list[AdminUserRow] = []
        for u in users:
            p = profiles.get(u.id)
            # Truth for the student columns is "has a student_profile row",
            # NOT selected_persona_kind — the persona field defaults to
            # "professional" for accounts not created through the student
            # register flow, so gating on it hides real wizard progress
            # for legacy or admin-seeded users.
            has_linkedin: bool | None
            has_github: bool | None
            has_downloaded_cv: bool | None
            if p is not None:
                links = p.links or {}
                has_linkedin = bool((links.get("linkedin") or "").strip())
                has_github = bool((links.get("github") or "").strip())
                has_downloaded_cv = u.id in downloaded_ids
            else:
                has_linkedin = None
                has_github = None
                has_downloaded_cv = None
            # Prefer the student's wizard name — many students register
            # via OTP with no name field, then fill their name in the
            # Basics step, so `users.full_name` stays NULL while
            # `student_profile.full_name` has the real name. Falling
            # back to profile matches what the CV / emails show.
            display_name = (p.full_name if p and p.full_name else u.full_name)
            rows.append(
                AdminUserRow(
                    id=u.id,
                    email=u.email,
                    full_name=display_name,
                    persona_kind=u.selected_persona_kind,
                    is_active=u.is_active,
                    is_superuser=u.is_superuser,
                    email_verified=u.email_verified_at is not None,
                    last_login_at=u.last_login_at,
                    created_at=u.created_at,
                    wizard_step=p.current_step if p else None,
                    wizard_completed=len(p.completed_steps or []) if p else 0,
                    has_linkedin=has_linkedin,
                    has_github=has_github,
                    has_downloaded_cv=has_downloaded_cv,
                )
            )
        return rows, total

    async def list_user_entries(
        self, user_id: UUID, *, kind: str | None = None
    ) -> list[AdminEntryDetail]:
        """Return a user's StudentProfileEntry rows, optionally filtered
        by kind. Used by the LLM-audit panel on AdminUserDetail so
        admins can inspect what students typed AND what the LLM
        produced (details.ai_summary + details.ai_bullets) without
        impersonating the student.
        """
        q = select(StudentProfileEntry).where(
            StudentProfileEntry.user_id == user_id
        )
        if kind:
            q = q.where(StudentProfileEntry.kind == kind)
        q = q.order_by(
            StudentProfileEntry.sort_order,
            StudentProfileEntry.created_at.desc(),
        )
        rows = (await self._session.execute(q)).scalars().all()
        return [AdminEntryDetail.model_validate(r) for r in rows]

    async def get_user_detail(self, user_id: UUID) -> AdminUserDetail | None:
        u = await self._session.get(User, user_id)
        if u is None:
            return None
        # Same truth as list_users: presence of a student_profile row, not
        # the persona_kind flag (which is stale for many older accounts).
        student: AdminStudentSummary | None = None
        profile = await self._session.get(StudentProfile, user_id)
        if profile is not None:
            # Count entries + break down by kind
            entry_rows = (
                await self._session.execute(
                    select(
                        StudentProfileEntry.kind,
                        func.count(StudentProfileEntry.id),
                    )
                    .where(StudentProfileEntry.user_id == user_id)
                    .group_by(StudentProfileEntry.kind)
                )
            ).all()
            by_kind = {k: c for (k, c) in entry_rows}
            student = AdminStudentSummary(
                full_name=profile.full_name,
                professional_email=profile.professional_email,
                phone=profile.phone,
                location=profile.location,
                date_of_birth=profile.date_of_birth,
                college=profile.college,
                department=profile.department,
                degree=profile.degree,
                major=profile.major,
                graduation_year=profile.graduation_year,
                gpa=str(profile.gpa) if profile.gpa is not None else None,
                headline=profile.headline,
                summary=profile.summary,
                links=dict(profile.links or {}),
                interests=list(profile.interests or []),
                completed_steps=list(profile.completed_steps or []),
                current_step=profile.current_step,
                cv_template_slug=profile.cv_template_slug,
                photo_file_id=profile.photo_file_id,
                entries_count=sum(by_kind.values()),
                entries_by_kind=by_kind,
                updated_at=profile.updated_at,
            )
        # Same fallback as list_users — wizard-supplied name wins over
        # a NULL users.full_name (common for OTP-registered students).
        display_name = (
            profile.full_name if profile and profile.full_name else u.full_name
        )
        return AdminUserDetail(
            id=u.id,
            email=u.email,
            full_name=display_name,
            persona_kind=u.selected_persona_kind,
            is_active=u.is_active,
            is_superuser=u.is_superuser,
            email_verified_at=u.email_verified_at,
            last_login_at=u.last_login_at,
            created_at=u.created_at,
            student=student,
        )

    # ---- Mutations ----------------------------------------------------

    async def set_user_active(self, user_id: UUID, active: bool) -> bool:
        u = await self._session.get(User, user_id)
        if u is None:
            return False
        u.is_active = active
        await self._session.commit()
        return True

    async def reset_wizard_progress(self, user_id: UUID) -> bool:
        p = await self._session.get(StudentProfile, user_id)
        if p is None:
            return False
        p.completed_steps = []
        p.current_step = None
        await self._session.commit()
        return True

    async def delete_user(self, user_id: UUID) -> bool:
        # Cascading FKs on students, entries, otp codes, personas, etc.
        # UsageEvent.user_id is SET NULL — history survives the delete.
        u = await self._session.get(User, user_id)
        if u is None:
            return False
        await self._session.execute(delete(User).where(User.id == user_id))
        await self._session.commit()
        return True

    # ---- Activity -----------------------------------------------------

    async def list_activity(
        self,
        *,
        kind: str | None,
        status_: str | None,
        page: int,
        size: int,
    ) -> tuple[list[AdminActivityRow], int]:
        q = select(UsageEvent, User.email).outerjoin(
            User, User.id == UsageEvent.user_id
        )
        if kind:
            q = q.where(UsageEvent.kind == kind)
        if status_:
            q = q.where(UsageEvent.status == status_)

        # Count against the same predicate
        count_q = select(func.count(UsageEvent.id))
        if kind:
            count_q = count_q.where(UsageEvent.kind == kind)
        if status_:
            count_q = count_q.where(UsageEvent.status == status_)
        total = await self._scalar(count_q)

        q = q.order_by(UsageEvent.created_at.desc()).offset(
            (page - 1) * size
        ).limit(size)
        result = (await self._session.execute(q)).all()
        rows: list[AdminActivityRow] = []
        for ev, email in result:
            rows.append(
                AdminActivityRow(
                    id=ev.id,
                    user_id=ev.user_id,
                    user_email=email,
                    kind=ev.kind,
                    status=ev.status,  # type: ignore[arg-type]
                    duration_ms=ev.duration_ms,
                    error_message=ev.error_message,
                    meta=dict(ev.meta or {}),
                    created_at=ev.created_at,
                )
            )
        return rows, total

    # ---- Templated emails --------------------------------------------

    async def _load_user_bundle(
        self, user_id: UUID
    ) -> tuple[User, StudentProfile | None] | None:
        """Fetch a user + optional student profile in one round-trip."""
        u = await self._session.get(User, user_id)
        if u is None:
            return None
        # Always try to load — presence of a student_profile row is the
        # truth for "has CV data", not the persona_kind flag.
        p = await self._session.get(StudentProfile, user_id)
        return u, p

    def _build_template_context(
        self, user: User, profile: StudentProfile | None, settings: Settings
    ) -> dict[str, str]:
        """Populate every placeholder any template might reference.

        `_SafeDict` in the renderer leaves missing keys as literal `{key}`
        text — populate everything, even fields the first template
        doesn't use, so future templates just work.
        """
        student_name = profile.full_name if profile else None
        full_name = student_name or user.full_name or user.email
        first_name = (full_name or "there").strip().split()[0] if full_name else "there"
        links = (profile.links or {}) if profile else {}
        app_url = settings.frontend_base_url.rstrip("/")
        return {
            "first_name": first_name,
            "full_name": full_name or "",
            "email": user.email,
            "app_name": settings.app_name,
            "app_url": app_url,
            "feedback_url": f"{app_url}/feedback",
            "college": (profile.college if profile else "") or "",
            "major": (profile.major if profile else "") or "",
            "graduation_year": (
                str(profile.graduation_year)
                if profile and profile.graduation_year
                else ""
            ),
            "linkedin_url": (links.get("linkedin") or "") if links else "",
            "github_url": (links.get("github") or "") if links else "",
        }

    def _render_email(
        self,
        *,
        template: EmailTemplateSpec,
        user: User,
        profile: StudentProfile | None,
        settings: Settings,
    ) -> tuple[str, str, str]:
        """Return (subject, html, text) with placeholders substituted.

        Templates are named `{template.id}.html` / `.txt` in the email
        templates dir. Subject line goes through the same _SafeDict pass.
        """
        ctx = self._build_template_context(user, profile, settings)
        # Subject uses the same _SafeDict semantics so a stray placeholder
        # doesn't blow up — reuse render() via a temporary file? No —
        # simpler: format_map directly. Import kept local to avoid a
        # rerouted dep.
        from app.infrastructure.email.template_renderer import _SafeDict
        subject = template.subject.format_map(_SafeDict(ctx))
        html = render(f"{template.id}.html", ctx)
        text = render(f"{template.id}.txt", ctx)
        return subject, html, text

    async def _most_recent_template_send(
        self, user_id: UUID, template_id: str, *, within: timedelta
    ) -> datetime | None:
        """Look up the audit trail for a matching send inside the window.

        Audit rows written by `_audit(actor, "send_email", user_id,
        meta={"template": template_id})` in admin.py — we key off those.
        """
        since = datetime.now(UTC) - within
        stmt = (
            select(UsageEvent.created_at)
            .where(UsageEvent.kind == "admin.action")
            .where(UsageEvent.meta.op("->>")("action") == "send_email")
            .where(UsageEvent.meta.op("->>")("template") == template_id)
            .where(UsageEvent.meta.op("->>")("target_user_id") == str(user_id))
            .where(UsageEvent.created_at >= since)
            .order_by(UsageEvent.created_at.desc())
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def preview_email_for_user(
        self, *, user_id: UUID, template_id: str, settings: Settings
    ) -> EmailPreviewResponse | None:
        """Render the email for admin preview + return the recent-send hint."""
        template = get_template(template_id)
        if template is None:
            return None
        bundle = await self._load_user_bundle(user_id)
        if bundle is None:
            return None
        user, profile = bundle
        subject, html, text = self._render_email(
            template=template, user=user, profile=profile, settings=settings
        )
        recent = await self._most_recent_template_send(
            user_id, template_id, within=timedelta(days=7)
        )
        recipient_name = (profile.full_name if profile else None) or user.full_name
        return EmailPreviewResponse(
            subject=subject,
            html=html,
            text=text,
            recipient_email=user.email,
            recipient_name=recipient_name,
            recent_send_at=recent,
        )

    async def build_email_message_for_user(
        self, *, user_id: UUID, template_id: str, settings: Settings
    ) -> EmailMessage | None:
        """Build the outgoing message; caller pushes it through the provider."""
        template = get_template(template_id)
        if template is None:
            return None
        bundle = await self._load_user_bundle(user_id)
        if bundle is None:
            return None
        user, profile = bundle
        subject, html, text = self._render_email(
            template=template, user=user, profile=profile, settings=settings
        )
        return EmailMessage(
            to=user.email,
            subject=subject,
            html_body=html,
            text_body=text,
            tags={"kind": "admin", "template": template_id},
        )

    async def bulk_dry_run(
        self, *, user_ids: list[UUID], template_id: str
    ) -> list[BulkRecipient]:
        """Preview recipient list with recent-send flag per user."""
        if get_template(template_id) is None:
            return []
        # One round-trip for users.
        users = (
            await self._session.execute(
                select(User).where(User.id.in_(user_ids))
            )
        ).scalars().all()
        by_id: dict[UUID, User] = {u.id: u for u in users}
        # One round-trip for student profiles — used to fall back to
        # the wizard-supplied name when users.full_name is NULL.
        profile_rows = (
            await self._session.execute(
                select(StudentProfile).where(StudentProfile.user_id.in_(user_ids))
            )
        ).scalars().all()
        profile_by_id: dict[UUID, StudentProfile] = {p.user_id: p for p in profile_rows}
        # One round-trip for the audit hits in the last 7 days.
        since = datetime.now(UTC) - timedelta(days=7)
        stmt = (
            select(UsageEvent.meta.op("->>")("target_user_id"))
            .where(UsageEvent.kind == "admin.action")
            .where(UsageEvent.meta.op("->>")("action") == "send_email")
            .where(UsageEvent.meta.op("->>")("template") == template_id)
            .where(UsageEvent.created_at >= since)
        )
        recent_ids = {
            row for (row,) in (await self._session.execute(stmt)).all() if row
        }
        # Preserve requested order; skip unknown ids.
        out: list[BulkRecipient] = []
        for uid in user_ids:
            u = by_id.get(uid)
            if u is None:
                continue
            profile = profile_by_id.get(uid)
            display_name = (
                profile.full_name if profile and profile.full_name else u.full_name
            )
            out.append(
                BulkRecipient(
                    user_id=uid,
                    email=u.email,
                    full_name=display_name,
                    has_recent_send=str(uid) in recent_ids,
                )
            )
        return out

    # ---- Internals ----------------------------------------------------

    async def _scalar(self, stmt: Any) -> int:
        v = (await self._session.execute(stmt)).scalar()
        return int(v or 0)
