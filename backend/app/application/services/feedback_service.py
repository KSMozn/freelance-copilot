"""FeedbackService — writes a `feedback_entries` row + notifies admins.

Two entry points:

  * `submit_general(user_id, message)` — from the /feedback page. Every
    submission also fires an *immediate* email to every active admin so
    urgent complaints don't wait for the daily digest.
  * `submit_survey(user_id, rating, comment, template_slug)` — from the
    post-download star card. NO immediate email; these roll into the
    daily report as aggregate + a line per response.

The immediate-email send is fire-and-forget via `asyncio.create_task`
(same shape as `usage_event_service.fire`) so a slow Resend call can't
tie up the request thread. Failures are swallowed but logged.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domain.providers.blob_store import BlobStore
from app.domain.providers.email_provider import EmailMessage, EmailProvider
from app.infrastructure.db.models.admin_user import AdminUser
from app.infrastructure.db.models.feedback_entry import FeedbackEntry
from app.infrastructure.db.models.user import User
from app.infrastructure.email.template_renderer import render
from app.infrastructure.storage.uploaded_file_store import store_uploaded_file

ScreenshotUpload = tuple[str, str, bytes]

logger = logging.getLogger(__name__)

_BG_TASKS: set[asyncio.Task[Any]] = set()


class FeedbackService:
    def __init__(
        self,
        session: AsyncSession,
        email_provider: EmailProvider,
        blob_store: BlobStore,
    ) -> None:
        self._session = session
        self._email = email_provider
        self._blobs = blob_store

    async def submit_general(
        self,
        user_id: UUID,
        message: str,
        *,
        screenshot: ScreenshotUpload | None = None,
    ) -> FeedbackEntry:
        screenshot_file_id = None
        if screenshot is not None:
            filename, content_type, content = screenshot
            file_row = await store_uploaded_file(
                self._session,
                self._blobs,
                user_id=user_id,
                prefix="feedback-screenshots",
                filename=filename,
                content_type=content_type,
                content=content,
            )
            screenshot_file_id = file_row.id

        row = FeedbackEntry(
            user_id=user_id,
            kind="general",
            message=message,
            screenshot_file_id=screenshot_file_id,
        )
        self._session.add(row)
        await self._session.flush()

        submitter = await self._session.get(User, user_id)
        submitter_email = submitter.email if submitter else "(unknown)"

        payload = {
            "submitter_email": submitter_email,
            "message": message,
            "created_at_iso": row.created_at.isoformat()
            if row.created_at
            else "",
        }
        recipients = await self._active_admin_emails()
        task = asyncio.create_task(
            self._notify_admins(recipients, payload)
        )
        _BG_TASKS.add(task)
        task.add_done_callback(_BG_TASKS.discard)

        return row

    async def submit_survey(
        self,
        user_id: UUID,
        rating: int,
        comment: str | None,
        template_slug: str | None,
    ) -> FeedbackEntry:
        row = FeedbackEntry(
            user_id=user_id,
            kind="post_download",
            rating=rating,
            message=comment,
            template_slug=template_slug,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    # ---- helpers -----------------------------------------------------

    async def _active_admin_emails(self) -> list[str]:
        rows = await self._session.execute(
            select(AdminUser.email).where(AdminUser.is_active.is_(True))
        )
        return [e for (e,) in rows.all()]

    async def _notify_admins(
        self, recipients: list[str], payload: dict[str, str]
    ) -> None:
        if not recipients:
            return
        s = get_settings()
        context = {
            "app_name": s.app_name,
            "submitter_email": payload["submitter_email"],
            "message": payload["message"],
            "created_at": payload["created_at_iso"],
            "admin_url": s.admin_base_url,
        }
        subject = f"[{s.app_name}] New feedback from {payload['submitter_email']}"
        try:
            html = render("feedback_notification.html", context)
            text = render("feedback_notification.txt", context)
        except Exception:
            logger.exception("Failed to render feedback notification template")
            return
        for to in recipients:
            try:
                await self._email.send(
                    EmailMessage(
                        to=to,
                        subject=subject,
                        html_body=html,
                        text_body=text,
                        tags={"kind": "feedback_notification"},
                    )
                )
            except Exception:
                # Never let one recipient's failure block the rest.
                logger.exception("Failed to send feedback notification to %s", to)
