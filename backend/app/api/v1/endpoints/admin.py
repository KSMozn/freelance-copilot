"""Admin panel endpoints — /api/v1/admin/*.

Every route gated by `CurrentAdmin`. Mutations always emit an
`admin.action` usage_event so we have an audit trail per superuser
action.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select

from app.application.dto.admin_dto import (
    AdminActionResult,
    AdminActivityResponse,
    AdminCvTemplateListResponse,
    AdminCvTemplateRead,
    AdminCvTemplateUpdate,
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
    SendEmailBulkDryRunResponse,
    SendEmailBulkRequest,
    SendEmailBulkResponse,
    SendEmailRequest,
)
from app.application.dto.feedback_dto import FeedbackListResponse, FeedbackRead
from app.application.email_templates import EmailTemplateSpec, get_template, list_templates
from app.application.services import usage_event_service
from app.application.services.admin_service import AdminService
from app.application.services.cv_template_service import CvTemplateService
from app.application.services.daily_report_service import DailyReportService
from app.core.config import Settings, get_settings
from app.core.deps import CurrentAdmin, SessionDep, get_email_provider
from app.core.security import create_access_token, create_refresh_token
from app.domain.entities.admin_user import AdminUser as AdminUserEntity
from app.domain.providers.email_provider import EmailProvider
from app.infrastructure.db.models.feedback_entry import FeedbackEntry
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
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=200),
) -> AdminUserListResponse:
    items, total = await svc.list_users(search=search, page=page, size=size)
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
    # Mint tokens for the target — no password check, admin-level trust.
    access = create_access_token(user_id)
    refresh = create_refresh_token(user_id)
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
        refresh_token=refresh,
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


# ---- Feedback list ------------------------------------------------------


@router.get("/feedback", response_model=FeedbackListResponse)
async def list_feedback(
    _: CurrentAdmin,
    session: SessionDep,
    kind: str | None = Query(default=None, pattern="^(general|post_download)$"),
    since: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> FeedbackListResponse:
    stmt = select(FeedbackEntry).order_by(FeedbackEntry.created_at.desc())
    if kind:
        stmt = stmt.where(FeedbackEntry.kind == kind)
    if since:
        stmt = stmt.where(FeedbackEntry.created_at >= since)
    stmt = stmt.limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    return FeedbackListResponse(
        items=[FeedbackRead.model_validate(r) for r in rows],
        total=len(rows),
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
    configured, the check is skipped so we can trigger locally.
    """
    expected = get_settings().report_task_secret
    if expected:
        if x_task_secret != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid task secret",
            )
    svc = DailyReportService(session, email_provider)
    report = await svc.build_report(window_hours=payload.window_hours)
    return await svc.send(report)
