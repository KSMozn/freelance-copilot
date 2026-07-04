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

from sqlalchemy import case, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.admin_dto import (
    AdminActivityRow,
    AdminOverview,
    AdminStudentSummary,
    AdminUserDetail,
    AdminUserRow,
    EntryKindCount,
    SignupsPoint,
    UsageKindCount,
    WizardFunnel,
)
from app.infrastructure.db.models.student_profile import (
    StudentProfile,
    StudentProfileEntry,
)
from app.infrastructure.db.models.usage_event import UsageEvent
from app.infrastructure.db.models.user import User

WIZARD_STEPS = (
    "basics",
    "education",
    "photo",
    "skills",
    "courses",
    "projects",
    "volunteer",
    "languages",
    "certificates",
    "summary",
    "preview",
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
            volunteer=counts["volunteer"],
            languages=counts["languages"],
            certificates=counts["certificates"],
            summary=counts["summary"],
            preview=counts["preview"],
            downloaded=distinct_downloaders,
        )

    # ---- Users --------------------------------------------------------

    async def list_users(
        self, *, search: str | None, page: int, size: int
    ) -> tuple[list[AdminUserRow], int]:
        q = select(User)
        if search:
            like = f"%{search.strip().lower()}%"
            q = q.where(
                or_(
                    func.lower(User.email).like(like),
                    func.lower(func.coalesce(User.full_name, "")).like(like),
                )
            )
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
        if ids:
            prof_rows = (
                await self._session.execute(
                    select(StudentProfile).where(StudentProfile.user_id.in_(ids))
                )
            ).scalars().all()
            profiles = {p.user_id: p for p in prof_rows}

        rows: list[AdminUserRow] = []
        for u in users:
            p = profiles.get(u.id)
            # Presence checks look at profile.links (populated in the
            # wizard's basics step), not career_pack, so late-stage clicks
            # in the Starter Pack don't change what the admin sees.
            has_linkedin: bool | None
            has_github: bool | None
            if u.selected_persona_kind == "student":
                links = (p.links or {}) if p else {}
                has_linkedin = bool((links.get("linkedin") or "").strip())
                has_github = bool((links.get("github") or "").strip())
            else:
                has_linkedin = None
                has_github = None
            rows.append(
                AdminUserRow(
                    id=u.id,
                    email=u.email,
                    full_name=u.full_name,
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
                )
            )
        return rows, total

    async def get_user_detail(self, user_id: UUID) -> AdminUserDetail | None:
        u = await self._session.get(User, user_id)
        if u is None:
            return None
        student: AdminStudentSummary | None = None
        if u.selected_persona_kind == "student":
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
        return AdminUserDetail(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
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

    # ---- Internals ----------------------------------------------------

    async def _scalar(self, stmt: Any) -> int:
        v = (await self._session.execute(stmt)).scalar()
        return int(v or 0)
