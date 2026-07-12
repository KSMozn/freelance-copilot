"""Admin panel endpoints — /api/v1/admin/*.

Every route gated by `CurrentAdmin`. Mutations always emit an
`admin.action` usage_event so we have an audit trail per superuser
action.
"""
from __future__ import annotations

import logging
import secrets as _secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy import func, select

from app.application.dto.admin_dto import (
    AdminActionResult,
    AdminActivityResponse,
    AdminCvTemplateListResponse,
    AdminCvTemplateRead,
    AdminCvTemplateUpdate,
    AdminEmailSendRow,
    AdminEmailSendsResponse,
    AdminEntriesResponse,
    AdminImpersonateResponse,
    AdminOverview,
    AdminUserDeleteRequest,
    AdminUserDetail,
    AdminUserListResponse,
    BulkFailure,
    DailyReportRequest,
    DailyReportResult,
    EmailPreviewResponse,
    LlmCallRow,
    LlmCallsResponse,
    LlmSpendSummary,
    SendEmailBulkDryRunResponse,
    SendEmailBulkRequest,
    SendEmailBulkResponse,
    SendEmailRequest,
)
from app.application.dto.feedback_dto import AdminFeedbackItem, AdminFeedbackListResponse
from app.application.dto.student_dto import StudentProfileUpdate
from app.application.email_templates import EmailTemplateSpec, get_template, list_templates
from app.application.services import usage_event_service
from app.application.services.admin_service import AdminService
from app.application.services.cv_template_service import CvTemplateService
from app.application.services.daily_report_service import DailyReportService
from app.application.services.student_cv_docx_renderer import StudentCvDocxRenderer
from app.application.services.student_cv_renderer import StudentCvRenderer, WeasyPrintUnavailable
from app.application.services.student_profile_service import StudentProfileService
from app.core.config import Settings, get_settings
from app.core.deps import CurrentAdmin, SessionDep, get_blob_store, get_email_provider
from app.core.security import create_impersonation_token
from app.domain.entities.admin_user import AdminUser as AdminUserEntity
from app.domain.providers.blob_store import BlobStore
from app.domain.providers.email_provider import EmailProvider
from app.infrastructure.db.models.feedback_entry import FeedbackEntry
from app.infrastructure.db.models.usage_event import UsageEvent
from app.infrastructure.db.models.user import User
from app.infrastructure.email.errors import EmailProviderError

router = APIRouter(prefix="/admin", tags=["admin"])


def _service(session: SessionDep) -> AdminService:
    return AdminService(session)


AdminSvc = Annotated[AdminService, Depends(_service)]


# ---- Overview + Activity -----------------------------------------------


@router.get("/overview", response_model=AdminOverview)
async def overview(_: CurrentAdmin, svc: AdminSvc) -> AdminOverview:
    return await svc.get_overview()


@router.get("/activity", response_model=AdminActivityResponse)
async def activity(
    _: CurrentAdmin,
    svc: AdminSvc,
    kind: str | None = Query(default=None),
    status_: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
) -> AdminActivityResponse:
    items, total = await svc.list_activity(
        kind=kind, status_=status_, page=page, size=size
    )
    return AdminActivityResponse(items=items, total=total, page=page, size=size)


# ---- Users -------------------------------------------------------------


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    _: CurrentAdmin,
    svc: AdminSvc,
    search: str | None = Query(default=None),
    stuck_at: str | None = Query(default=None, max_length=32),
    persona: str | None = Query(default=None, pattern="^(student|professional)$"),
    active: bool | None = Query(default=None),
    email_verified: bool | None = Query(default=None),
    has_cv: bool | None = Query(default=None),
    college: str | None = Query(default=None, max_length=120),
    signed_up_after: datetime | None = Query(default=None),
    signed_up_before: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=200),
) -> AdminUserListResponse:
    items, total = await svc.list_users(
        search=search,
        page=page,
        size=size,
        stuck_at=stuck_at,
        persona=persona,
        active=active,
        email_verified=email_verified,
        has_cv=has_cv,
        college=college,
        signed_up_after=signed_up_after,
        signed_up_before=signed_up_before,
    )
    return AdminUserListResponse(items=items, total=total, page=page, size=size)


@router.get("/users/{user_id}", response_model=AdminUserDetail)
async def get_user(user_id: UUID, _: CurrentAdmin, svc: AdminSvc) -> AdminUserDetail:
    detail = await svc.get_user_detail(user_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return detail


@router.get("/users/{user_id}/entries", response_model=AdminEntriesResponse)
async def get_user_entries(
    user_id: UUID,
    _: CurrentAdmin,
    svc: AdminSvc,
    kind: str | None = Query(default=None, max_length=32),
) -> AdminEntriesResponse:
    """Read-only listing of a user's entries — surfaces raw + AI-
    generated content on `details` so admins can audit LLM output
    (internship bullets, project narratives) without impersonating.
    """
    items = await svc.list_user_entries(user_id, kind=kind)
    return AdminEntriesResponse(items=items)


# ---- Edit student profile fields ---------------------------------------


@router.patch("/users/{user_id}/student-profile", response_model=AdminUserDetail)
async def edit_student_profile(
    user_id: UUID,
    payload: StudentProfileUpdate,
    actor: CurrentAdmin,
    svc: AdminSvc,
    session: SessionDep,
    blobs: Annotated[BlobStore, Depends(get_blob_store)],
) -> AdminUserDetail:
    """Admin-side edit of the student_profile row.

    Support-case: student typoed their email, entered a fake phone,
    picked the wrong graduation year. Previously the only fix was
    impersonation. Uses the same DTO + service the wizard uses, so
    validation is identical. Records which fields changed in the
    audit meta so an admin can't silently rewrite content.
    """
    detail = await svc.get_user_detail(user_id)
    if detail is None or detail.student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found"
        )
    changed = payload.model_dump(exclude_unset=True)
    if not changed:
        return detail
    student_svc = StudentProfileService(session, blobs)
    await student_svc.upsert_profile(user_id, payload)
    updated = await svc.get_user_detail(user_id)
    _audit(
        actor,
        "edit_student_profile",
        user_id,
        extra={"changed_fields": sorted(changed.keys())},
    )
    return updated  # type: ignore[return-value]


# ---- LLM call drill-down ----------------------------------------------


@router.get("/llm-calls", response_model=LlmCallsResponse)
async def list_llm_calls(
    _: CurrentAdmin,
    session: SessionDep,
    model: str | None = Query(default=None, max_length=120),
    user_id: UUID | None = Query(default=None),
    since_days: int = Query(default=30, ge=1, le=90),
    limit: int = Query(default=200, ge=1, le=1000),
) -> LlmCallsResponse:
    """Per-call breakdown backing the LLM spend drill-down cards.

    Reads the same rows the aggregation counts (`usage_events` with
    `meta.prompt_tokens`), optionally filtered by model and/or by
    user_id. Joins to users for the recipient email so the operator
    sees who ran what. Default window is 30 days.
    """
    since = datetime.now(tz=UTC) - timedelta(days=since_days)
    stmt = (
        select(UsageEvent)
        .where(UsageEvent.created_at >= since)
        .where(UsageEvent.meta.op("?")("prompt_tokens"))
        .order_by(UsageEvent.created_at.desc())
    )
    if model:
        stmt = stmt.where(UsageEvent.meta.op("->>")("model") == model)
    if user_id is not None:
        stmt = stmt.where(UsageEvent.user_id == user_id)
    stmt = stmt.limit(limit)
    events = (await session.execute(stmt)).scalars().all()

    user_ids = {e.user_id for e in events if e.user_id is not None}
    users_by_id: dict[UUID, User] = {}
    if user_ids:
        rows = (
            await session.execute(select(User).where(User.id.in_(user_ids)))
        ).scalars().all()
        users_by_id = {u.id: u for u in rows}

    items: list[LlmCallRow] = []
    total_cost = 0.0
    for ev in events:
        meta = ev.meta or {}
        pt = _int_or_zero(meta.get("prompt_tokens"))
        ct = _int_or_zero(meta.get("completion_tokens"))
        tt = _int_or_zero(meta.get("total_tokens")) or (pt + ct)
        cost_raw = meta.get("cost_usd")
        cost = float(cost_raw) if isinstance(cost_raw, int | float) else None
        if cost is not None:
            total_cost += cost
        target = users_by_id.get(ev.user_id) if ev.user_id else None
        items.append(
            LlmCallRow(
                id=ev.id,
                created_at=ev.created_at,
                kind=ev.kind,
                status=ev.status,
                user_id=ev.user_id,
                user_email=target.email if target else None,
                prompt_tokens=pt,
                completion_tokens=ct,
                total_tokens=tt,
                cost_usd=cost,
                model=str(meta.get("model")) if isinstance(meta.get("model"), str) else None,
                provider=str(meta.get("provider")) if isinstance(meta.get("provider"), str) else None,
                duration_ms=ev.duration_ms,
            )
        )
    return LlmCallsResponse(
        items=items, total=len(items), total_cost_usd=round(total_cost, 6)
    )


def _int_or_zero(v: object) -> int:
    return int(v) if isinstance(v, int | float) else 0


@router.get("/users/{user_id}/llm-spend", response_model=LlmSpendSummary)
async def get_user_llm_spend(
    user_id: UUID,
    _: CurrentAdmin,
    svc: AdminSvc,
    since_days: int = Query(default=30, ge=1, le=90),
) -> LlmSpendSummary:
    """User-scoped LLM spend for the admin user-detail card.

    Mirror of the Overview LLM spend card, but scoped to one user's
    coach/career_pack calls in the last N days (default 30).
    """
    return await svc.compute_user_llm_spend(user_id, since_days=since_days)


# ---- CV preview / download (as admin) ----------------------------------


async def _load_target_photo(
    svc: StudentProfileService, user_id: UUID
) -> tuple[bytes | None, str | None]:
    payload = await svc.get_photo(user_id)
    if payload is None:
        return None, None
    file_row, data = payload
    return data, file_row.content_type


def _cv_filename(profile_full_name: str | None) -> str:
    return (profile_full_name or "cv").replace(" ", "_")


@router.get("/users/{user_id}/cv/preview")
async def preview_user_cv_html(
    user_id: UUID,
    actor: CurrentAdmin,
    session: SessionDep,
    blobs: Annotated[BlobStore, Depends(get_blob_store)],
    template: str | None = Query(default=None, max_length=64),
) -> dict[str, str]:
    """HTML preview of a user's CV as it would render for them.

    No impersonation, no side effects on the user's session. Used by the
    admin user-detail page's Preview CV card. Audit event fires so we
    know an admin looked.
    """
    student_svc = StudentProfileService(session, blobs)
    profile, entries = await student_svc.load_profile_bundle(user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No profile")
    photo_bytes, photo_mime = await _load_target_photo(student_svc, user_id)
    slug = await CvTemplateService(session).resolve_slug(
        requested=template,
        profile_slug=profile.cv_template_slug,
    )
    html = StudentCvRenderer().render_html(
        profile=profile,
        entries=entries,
        photo_bytes=photo_bytes,
        photo_mime=photo_mime,
        template_slug=slug,
    )
    _audit(actor, "preview_cv", user_id, extra={"template": slug})
    return {"html": html, "template_slug": slug}


@router.get("/users/{user_id}/cv.pdf")
async def download_user_cv_pdf(
    user_id: UUID,
    actor: CurrentAdmin,
    session: SessionDep,
    blobs: Annotated[BlobStore, Depends(get_blob_store)],
    template: str | None = Query(default=None, max_length=64),
) -> Response:
    student_svc = StudentProfileService(session, blobs)
    profile, entries = await student_svc.load_profile_bundle(user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No profile")
    photo_bytes, photo_mime = await _load_target_photo(student_svc, user_id)
    slug = await CvTemplateService(session).resolve_slug(
        requested=template,
        profile_slug=profile.cv_template_slug,
    )
    try:
        pdf = StudentCvRenderer().render_pdf(
            profile=profile,
            entries=entries,
            photo_bytes=photo_bytes,
            photo_mime=photo_mime,
            template_slug=slug,
        )
    except WeasyPrintUnavailable as exc:
        _audit(actor, "download_cv_pdf", user_id, ok=False, extra={"template": slug})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    filename = _cv_filename(profile.full_name)
    _audit(
        actor,
        "download_cv_pdf",
        user_id,
        extra={"template": slug, "size_bytes": len(pdf)},
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
    )


@router.get("/users/{user_id}/cv.docx")
async def download_user_cv_docx(
    user_id: UUID,
    actor: CurrentAdmin,
    session: SessionDep,
    blobs: Annotated[BlobStore, Depends(get_blob_store)],
    template: str | None = Query(default=None, max_length=64),
) -> Response:
    student_svc = StudentProfileService(session, blobs)
    profile, entries = await student_svc.load_profile_bundle(user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No profile")
    photo_bytes, photo_mime = await _load_target_photo(student_svc, user_id)
    slug = await CvTemplateService(session).resolve_slug(
        requested=template,
        profile_slug=profile.cv_template_slug,
    )
    try:
        docx_bytes = StudentCvDocxRenderer().render_docx(
            profile=profile,
            entries=entries,
            photo_bytes=photo_bytes,
            photo_mime=photo_mime,
            template_slug=slug,
        )
    except Exception as exc:
        _audit(actor, "download_cv_docx", user_id, ok=False, extra={"template": slug})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not build DOCX",
        ) from exc
    filename = _cv_filename(profile.full_name)
    _audit(
        actor,
        "download_cv_docx",
        user_id,
        extra={"template": slug, "size_bytes": len(docx_bytes)},
    )
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}_CV.docx"'},
    )


# ---- Actions -----------------------------------------------------------


def _audit(
    actor: AdminUserEntity,
    action: str,
    target_id: UUID,
    ok: bool = True,
    extra: dict[str, Any] | None = None,
) -> None:
    # user_id stays None because admin_users.id can't satisfy the FK to
    # users.id — the actor identity travels in `meta` instead. `extra`
    # merges into meta so callers can stash action-specific fields
    # (e.g. `template` for send_email).
    meta: dict[str, Any] = {
        "action": action,
        "target_user_id": str(target_id),
        "actor_admin_id": str(actor.id),
        "actor_email": actor.email,
    }
    if extra:
        meta.update(extra)
    usage_event_service.fire(
        user_id=None,
        kind="admin.action",
        status="ok" if ok else "error",
        meta=meta,
    )


@router.post("/users/{user_id}/enable", response_model=AdminActionResult)
async def enable_user(
    user_id: UUID, actor: CurrentAdmin, svc: AdminSvc
) -> AdminActionResult:
    ok = await svc.set_user_active(user_id, active=True)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    _audit(actor, "enable", user_id)
    return AdminActionResult(message="User enabled")


@router.post("/users/{user_id}/disable", response_model=AdminActionResult)
async def disable_user(
    user_id: UUID, actor: CurrentAdmin, svc: AdminSvc
) -> AdminActionResult:
    # actor is an admin_user; user_id is a users.id — separate spaces,
    # so a self-disable is now structurally impossible. No self-check
    # needed.
    ok = await svc.set_user_active(user_id, active=False)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    _audit(actor, "disable", user_id)
    return AdminActionResult(message="User disabled")


@router.post("/users/{user_id}/reset-wizard", response_model=AdminActionResult)
async def reset_wizard(
    user_id: UUID, actor: CurrentAdmin, svc: AdminSvc
) -> AdminActionResult:
    ok = await svc.reset_wizard_progress(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Student profile not found")
    _audit(actor, "reset_wizard", user_id)
    return AdminActionResult(message="Wizard progress reset")


@router.post("/users/{user_id}/impersonate", response_model=AdminImpersonateResponse)
async def impersonate(
    user_id: UUID, actor: CurrentAdmin, svc: AdminSvc
) -> AdminImpersonateResponse:
    detail = await svc.get_user_detail(user_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="User not found")
    # Mint a short-lived, non-refreshable token for the target — no password
    # check, admin-level trust. It carries an `act` claim naming the admin and
    # self-expires (see impersonation_token_expire_minutes), so an abandoned
    # "view as user" session can't linger. No refresh token is issued: the
    # empty string tells the frontend there's nothing to refresh, so the
    # session simply ends when the access token expires.
    access = create_impersonation_token(
        user_id, actor_admin_id=actor.id, actor_email=actor.email
    )
    usage_event_service.fire(
        user_id=None,
        kind="admin.impersonate",
        status="ok",
        meta={
            "actor_admin_id": str(actor.id),
            "actor_email": actor.email,
            "target_user_id": str(user_id),
            "target_email": detail.email,
        },
    )
    return AdminImpersonateResponse(
        target_user_id=user_id,
        target_user_email=detail.email,
        access_token=access,
        refresh_token="",
    )


@router.delete("/users/{user_id}", response_model=AdminActionResult)
async def delete_user(
    user_id: UUID,
    payload: AdminUserDeleteRequest,
    actor: CurrentAdmin,
    svc: AdminSvc,
) -> AdminActionResult:
    # actor is an admin_user; user_id is a users.id — separate spaces.
    detail = await svc.get_user_detail(user_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="User not found")
    if str(payload.confirm_email).lower() != str(detail.email).lower():
        raise HTTPException(
            status_code=400,
            detail="Confirmation email does not match the target user's email",
        )
    await svc.delete_user(user_id)
    _audit(actor, "delete", user_id)
    return AdminActionResult(message=f"Deleted user {detail.email}")


# ---- Admin-triggered emails --------------------------------------------

SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/email-templates", response_model=list[EmailTemplateSpec])
async def list_email_templates(_: CurrentAdmin) -> list[EmailTemplateSpec]:
    return list_templates()


@router.get("/emails", response_model=AdminEmailSendsResponse)
async def list_email_sends(
    _: CurrentAdmin,
    session: SessionDep,
    template_id: str | None = Query(default=None, max_length=64),
    status_: str | None = Query(default=None, alias="status", pattern="^(ok|error)$"),
    limit: int = Query(default=100, ge=1, le=500),
) -> AdminEmailSendsResponse:
    """History of admin-triggered emails.

    Reads `admin.action(send_email)` rows straight out of `usage_events`
    (same source of truth the Activity page uses) and joins to the
    recipient user + resolves the template's display name so operators
    see human names not slugs.
    """
    stmt = (
        select(UsageEvent)
        .where(UsageEvent.kind == "admin.action")
        .where(UsageEvent.meta.op("->>")("action") == "send_email")
        .order_by(UsageEvent.created_at.desc())
    )
    if template_id:
        stmt = stmt.where(UsageEvent.meta.op("->>")("template") == template_id)
    if status_:
        stmt = stmt.where(UsageEvent.status == status_)
    stmt = stmt.limit(limit)
    events = (await session.execute(stmt)).scalars().all()

    # Resolve target users in one round-trip so the list doesn't
    # explode into N+1 queries when we ship 200 rows.
    target_uuids: set[UUID] = set()
    for ev in events:
        meta = ev.meta or {}
        tid = meta.get("target_user_id")
        if isinstance(tid, str):
            try:
                target_uuids.add(UUID(tid))
            except ValueError:
                pass
    users_by_id: dict[UUID, User] = {}
    if target_uuids:
        rows = (
            await session.execute(select(User).where(User.id.in_(target_uuids)))
        ).scalars().all()
        users_by_id = {u.id: u for u in rows}

    items: list[AdminEmailSendRow] = []
    for ev in events:
        meta = ev.meta or {}
        tid_raw = meta.get("target_user_id")
        target_uuid: UUID | None = None
        if isinstance(tid_raw, str):
            try:
                target_uuid = UUID(tid_raw)
            except ValueError:
                target_uuid = None
        target = users_by_id.get(target_uuid) if target_uuid else None
        template_slug = str(meta.get("template", "")) or ""
        spec = get_template(template_slug) if template_slug else None
        items.append(
            AdminEmailSendRow(
                id=ev.id,
                sent_at=ev.created_at,
                status=ev.status,
                template_id=template_slug,
                template_name=spec.name if spec else None,
                target_user_id=target_uuid,
                target_email=target.email if target else None,
                target_full_name=target.full_name if target else None,
                actor_email=meta.get("actor_email") if isinstance(meta.get("actor_email"), str) else None,
                error_message=ev.error_message,
            )
        )
    return AdminEmailSendsResponse(items=items, total=len(items))


@router.get(
    "/users/{user_id}/email-preview", response_model=EmailPreviewResponse
)
async def preview_email(
    user_id: UUID,
    _: CurrentAdmin,
    svc: AdminSvc,
    settings: SettingsDep,
    template_id: str = Query(..., min_length=1, max_length=64),
) -> EmailPreviewResponse:
    if get_template(template_id) is None:
        raise HTTPException(status_code=404, detail="Unknown template")
    preview = await svc.preview_email_for_user(
        user_id=user_id, template_id=template_id, settings=settings
    )
    if preview is None:
        raise HTTPException(status_code=404, detail="User not found")
    return preview


@router.post("/users/{user_id}/send-email", response_model=AdminActionResult)
async def send_email_to_user(
    user_id: UUID,
    payload: SendEmailRequest,
    actor: CurrentAdmin,
    svc: AdminSvc,
    settings: SettingsDep,
    email_provider: Annotated[EmailProvider, Depends(get_email_provider)],
) -> AdminActionResult:
    if get_template(payload.template_id) is None:
        raise HTTPException(status_code=404, detail="Unknown template")
    message = await svc.build_email_message_for_user(
        user_id=user_id, template_id=payload.template_id, settings=settings
    )
    if message is None:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        await email_provider.send(message)
    except EmailProviderError as exc:
        _audit(
            actor,
            "send_email",
            user_id,
            ok=False,
            extra={"template": payload.template_id, "error": str(exc)},
        )
        raise HTTPException(status_code=502, detail=f"Email failed: {exc}") from exc
    _audit(
        actor,
        "send_email",
        user_id,
        extra={"template": payload.template_id},
    )
    return AdminActionResult(message=f"Sent to {message.to}")


@router.post(
    "/users/send-email-bulk",
    response_model=SendEmailBulkResponse | SendEmailBulkDryRunResponse,
)
async def send_email_bulk(
    payload: SendEmailBulkRequest,
    actor: CurrentAdmin,
    svc: AdminSvc,
    settings: SettingsDep,
    email_provider: Annotated[EmailProvider, Depends(get_email_provider)],
) -> SendEmailBulkResponse | SendEmailBulkDryRunResponse:
    if get_template(payload.template_id) is None:
        raise HTTPException(status_code=404, detail="Unknown template")
    logger.info(
        "bulk_email requested: template=%s dry_run=%s users=%d actor=%s",
        payload.template_id,
        payload.dry_run,
        len(payload.user_ids),
        actor.email,
    )
    if payload.dry_run:
        recipients = await svc.bulk_dry_run(
            user_ids=payload.user_ids, template_id=payload.template_id
        )
        return SendEmailBulkDryRunResponse(
            template_id=payload.template_id, recipients=recipients
        )
    # Real send — best-effort per user; keep going on failures.
    sent = 0
    skipped = 0
    failed: list[BulkFailure] = []
    for uid in payload.user_ids:
        message = await svc.build_email_message_for_user(
            user_id=uid, template_id=payload.template_id, settings=settings
        )
        if message is None:
            skipped += 1
            logger.warning("bulk_email skip: no user/template for %s", uid)
            continue
        try:
            await email_provider.send(message)
        except EmailProviderError as exc:
            _audit(
                actor,
                "send_email",
                uid,
                ok=False,
                extra={"template": payload.template_id, "error": str(exc)},
            )
            failed.append(BulkFailure(user_id=uid, error=str(exc)))
            logger.warning("bulk_email fail: user=%s err=%s", uid, exc)
            continue
        _audit(
            actor,
            "send_email",
            uid,
            extra={"template": payload.template_id},
        )
        sent += 1
    logger.info(
        "bulk_email done: template=%s sent=%d skipped=%d failed=%d",
        payload.template_id,
        sent,
        skipped,
        len(failed),
    )
    return SendEmailBulkResponse(
        template_id=payload.template_id,
        sent=sent,
        skipped=skipped,
        failed=failed,
    )


# ---- CV templates ------------------------------------------------------


def _cv_svc(session: SessionDep) -> CvTemplateService:
    return CvTemplateService(session)


CvSvc = Annotated[CvTemplateService, Depends(_cv_svc)]


@router.get("/cv-templates", response_model=AdminCvTemplateListResponse)
async def list_cv_templates(
    _: CurrentAdmin, svc: CvSvc
) -> AdminCvTemplateListResponse:
    rows = await svc.list_all()
    return AdminCvTemplateListResponse(
        items=[AdminCvTemplateRead.model_validate(r) for r in rows]
    )


@router.patch("/cv-templates/{slug}", response_model=AdminCvTemplateRead)
async def update_cv_template(
    slug: str,
    payload: AdminCvTemplateUpdate,
    actor: CurrentAdmin,
    svc: CvSvc,
) -> AdminCvTemplateRead:
    row = await svc.update(
        slug,
        is_visible=payload.is_visible,
        sort_order=payload.sort_order,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Template not found")
    # Audit — reuse the admin.action pattern; target_user_id has no
    # meaning here, so drop the slug into meta instead.
    usage_event_service.fire(
        user_id=None,
        kind="admin.action",
        status="ok",
        meta={
            "action": "cv_template.update",
            "slug": slug,
            "changes": {
                k: v
                for k, v in {
                    "is_visible": payload.is_visible,
                    "sort_order": payload.sort_order,
                }.items()
                if v is not None
            },
            "actor_admin_id": str(actor.id),
            "actor_email": actor.email,
        },
    )
    return AdminCvTemplateRead.model_validate(row)


# ---- Feedback triage inbox ---------------------------------------------


@router.get("/feedback", response_model=AdminFeedbackListResponse)
async def list_feedback(
    _: CurrentAdmin,
    session: SessionDep,
    kind: str | None = Query(default=None, pattern="^(general|post_download)$"),
    since: datetime | None = Query(default=None),
    resolved: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> AdminFeedbackListResponse:
    """Triage inbox — joins to `users` so the operator sees who wrote it.

    `resolved=None` returns everything; `false` only unresolved; `true`
    only resolved. Unresolved count is computed once and returned
    alongside so the sidebar badge doesn't need a second round-trip.
    """
    stmt = (
        select(FeedbackEntry, User.email, User.full_name)
        .join(User, User.id == FeedbackEntry.user_id, isouter=True)
        .order_by(FeedbackEntry.created_at.desc())
    )
    if kind:
        stmt = stmt.where(FeedbackEntry.kind == kind)
    if since:
        stmt = stmt.where(FeedbackEntry.created_at >= since)
    if resolved is True:
        stmt = stmt.where(FeedbackEntry.resolved_at.is_not(None))
    elif resolved is False:
        stmt = stmt.where(FeedbackEntry.resolved_at.is_(None))
    stmt = stmt.limit(limit)
    rows = (await session.execute(stmt)).all()

    items: list[AdminFeedbackItem] = []
    for row_entry, row_email, row_name in rows:
        resolver_email = row_entry.meta.get("resolved_by_email") if row_entry.meta else None
        items.append(
            AdminFeedbackItem(
                id=row_entry.id,
                user_id=row_entry.user_id,
                user_email=row_email,
                user_full_name=row_name,
                kind=row_entry.kind,
                rating=row_entry.rating,
                message=row_entry.message,
                template_slug=row_entry.template_slug,
                created_at=row_entry.created_at,
                resolved_at=row_entry.resolved_at,
                resolved_by_email=resolver_email,
            )
        )

    unresolved_count = (
        await session.execute(
            select(func.count())
            .select_from(FeedbackEntry)
            .where(FeedbackEntry.resolved_at.is_(None))
        )
    ).scalar_one()

    return AdminFeedbackListResponse(
        items=items, total=len(items), unresolved_count=int(unresolved_count)
    )


@router.post("/feedback/{feedback_id}/resolve", response_model=AdminFeedbackItem)
async def resolve_feedback(
    feedback_id: UUID, actor: CurrentAdmin, session: SessionDep
) -> AdminFeedbackItem:
    row = (
        await session.execute(
            select(FeedbackEntry).where(FeedbackEntry.id == feedback_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    row.resolved_at = datetime.now(tz=UTC)
    row.meta = {
        **(row.meta or {}),
        "resolved_by_admin_id": str(actor.id),
        "resolved_by_email": actor.email,
    }
    await session.commit()
    await session.refresh(row)
    _audit(actor, "resolve_feedback", row.user_id, extra={"feedback_id": str(row.id)})

    user_row = (
        await session.execute(
            select(User.email, User.full_name).where(User.id == row.user_id)
        )
    ).one_or_none()
    return AdminFeedbackItem(
        id=row.id,
        user_id=row.user_id,
        user_email=user_row[0] if user_row else None,
        user_full_name=user_row[1] if user_row else None,
        kind=row.kind,
        rating=row.rating,
        message=row.message,
        template_slug=row.template_slug,
        created_at=row.created_at,
        resolved_at=row.resolved_at,
        resolved_by_email=actor.email,
    )


@router.post("/feedback/{feedback_id}/unresolve", response_model=AdminFeedbackItem)
async def unresolve_feedback(
    feedback_id: UUID, actor: CurrentAdmin, session: SessionDep
) -> AdminFeedbackItem:
    row = (
        await session.execute(
            select(FeedbackEntry).where(FeedbackEntry.id == feedback_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    row.resolved_at = None
    meta = dict(row.meta or {})
    meta.pop("resolved_by_admin_id", None)
    meta.pop("resolved_by_email", None)
    row.meta = meta
    await session.commit()
    await session.refresh(row)
    _audit(actor, "unresolve_feedback", row.user_id, extra={"feedback_id": str(row.id)})

    user_row = (
        await session.execute(
            select(User.email, User.full_name).where(User.id == row.user_id)
        )
    ).one_or_none()
    return AdminFeedbackItem(
        id=row.id,
        user_id=row.user_id,
        user_email=user_row[0] if user_row else None,
        user_full_name=user_row[1] if user_row else None,
        kind=row.kind,
        rating=row.rating,
        message=row.message,
        template_slug=row.template_slug,
        created_at=row.created_at,
        resolved_at=None,
        resolved_by_email=None,
    )


# ---- Daily report task --------------------------------------------------


@router.post("/tasks/daily-report", response_model=DailyReportResult)
async def run_daily_report(
    payload: DailyReportRequest,
    session: SessionDep,
    email_provider: Annotated[EmailProvider, Depends(get_email_provider)],
    x_task_secret: Annotated[str | None, Header(alias="X-Task-Secret")] = None,
) -> DailyReportResult:
    """Machine-called (Cloud Scheduler). No admin JWT here — the shared
    secret in `X-Task-Secret` is the auth. In dev, if the secret isn't
    configured, the check is skipped so we can trigger locally; in any
    deployed env a missing secret is a hard 503 (fail closed) rather than
    an open endpoint.
    """
    settings = get_settings()
    expected = settings.report_task_secret
    if not expected:
        if settings.environment != "development":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Task secret not configured",
            )
    elif not _secrets.compare_digest(x_task_secret or "", expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid task secret",
        )
    svc = DailyReportService(session, email_provider)
    report = await svc.build_report(window_hours=payload.window_hours)
    return await svc.send(report)
