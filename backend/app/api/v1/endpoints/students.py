"""Student persona endpoints — wizard CRUD + coaching + CV download.

Mounted under `/students`. The whole surface is gated by the JWT (a
logged-in user is always editing their own row). The wizard reaches them
in this order on first run:

  GET /students/profile          → resume where we left off (or empty)
  PUT /students/profile          → save per-step (partial payloads OK)
  POST /students/profile/photo   → upload + dedupe
  GET /students/profile/photo    → fetch for preview
  GET/POST/PUT/DELETE /students/entries[/{id}] → repeating items
  POST /students/coach/email     → rule-based check, suggestions
  POST /students/coach/photo     → vision check (LLM)
  POST /students/coach/text      → blurb rewrite (LLM)
  GET /students/cv/preview       → HTML for the in-app preview pane
  GET /students/cv.pdf           → download
"""
from __future__ import annotations

import time
from typing import Annotated, Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)

from app.api.uploads import read_upload_limited
from app.application.dto.feedback_dto import (
    FEEDBACK_MESSAGE_MAX_LEN,
    FEEDBACK_MESSAGE_MIN_LEN,
    FeedbackRead,
    SurveyCreate,
)
from app.application.dto.student_dto import (
    CvPreviewResponse,
    CvTemplateListResponse,
    CvTemplateRead,
    DraftSummaryResponse,
    EmailCoachRequest,
    EmailCoachResponse,
    InternshipCoachRequest,
    InternshipCoachResponse,
    PhotoCoachResponse,
    ProofreadResponse,
    StudentEntryListResponse,
    StudentEntryRead,
    StudentEntryUpsert,
    StudentProfileRead,
    StudentProfileUpdate,
    TextCoachRequest,
    TextCoachResponse,
)
from app.application.services import usage_event_service
from app.application.services.cv_template_service import CvTemplateService
from app.application.services.feedback_service import FeedbackService
from app.application.services.llm_cost import usage_meta as _usage_meta
from app.application.services.student_coach_service import StudentCoachService
from app.application.services.student_cv_docx_renderer import (
    StudentCvDocxRenderer,
)
from app.application.services.student_cv_renderer import (
    StudentCvRenderer,
    WeasyPrintUnavailable,
)
from app.application.services.student_profile_service import StudentProfileService
from app.core.deps import (
    CurrentUser,
    SessionDep,
    get_ai_provider,
    get_blob_store,
    get_email_provider,
)
from app.domain.providers.ai_provider import AIProvider
from app.domain.providers.blob_store import BlobStore
from app.domain.providers.email_provider import EmailProvider
from app.infrastructure.db.models.student_profile import (
    StudentProfile,
    StudentProfileEntry,
)

router = APIRouter(prefix="/students", tags=["student"])


def _emit(
    user_id: UUID,
    kind: str,
    start: float,
    *,
    error: str | None = None,
    meta: dict[str, Any] | None = None,
    coach: Any | None = None,
) -> None:
    """Small helper — fire a usage_event with duration + status. Used by
    coach + CV endpoints to power the admin activity view.

    Pass `coach=<StudentCoachService | CareerPackService>` to also log
    the token usage + estimated cost of the most recent LLM call the
    service performed. Silently no-ops if the service didn't call an
    LLM (e.g. `check_email` is pure rules).
    """
    dt = int((time.perf_counter() - start) * 1000)
    final_meta: dict[str, Any] = dict(meta or {})
    if coach is not None:
        final_meta.update(
            _usage_meta(
                usage=getattr(coach, "last_usage", None),
                model=getattr(coach, "last_model", None),
                provider=getattr(coach, "last_provider", None),
            )
        )
    usage_event_service.fire(
        user_id=user_id,
        kind=kind,
        status="error" if error else "ok",
        duration_ms=dt,
        error_message=error,
        meta=final_meta,
    )


MAX_PHOTO_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}

MAX_SCREENSHOT_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_SCREENSHOT_TYPES = {"image/png", "image/jpeg", "image/webp"}


def _profile_to_read(row: StudentProfile, *, photo_url: str | None) -> StudentProfileRead:
    return StudentProfileRead(
        user_id=row.user_id,
        full_name=row.full_name,
        professional_email=row.professional_email,
        phone=row.phone,
        location=row.location,
        date_of_birth=row.date_of_birth,
        college=row.college,
        department=row.department,
        degree=row.degree,
        major=row.major,
        graduation_year=row.graduation_year,
        gpa=row.gpa,
        photo_file_id=row.photo_file_id,
        photo_url=photo_url,
        photo_offset_x=row.photo_offset_x,
        photo_offset_y=row.photo_offset_y,
        photo_zoom=row.photo_zoom,
        summary=row.summary,
        headline=row.headline,
        links=dict(row.links or {}),
        interests=list(row.interests or []),
        completed_steps=list(row.completed_steps or []),
        current_step=row.current_step,
        cv_template_slug=row.cv_template_slug,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _entry_to_read(row: StudentProfileEntry) -> StudentEntryRead:
    return StudentEntryRead(
        id=row.id,
        kind=row.kind,
        title=row.title,
        organization=row.organization,
        start_date=row.start_date,
        end_date=row.end_date,
        is_current=row.is_current,
        description=row.description,
        url=row.url,
        details=dict(row.details or {}),
        sort_order=row.sort_order,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _photo_url_for(user_id: UUID, profile: StudentProfile | None) -> str | None:
    """Return a relative-to-API-base path the frontend can prepend.

    The browser can't send the JWT through a plain `<img src>`, so the
    frontend actually loads the photo via axios + blob URL — but we still
    return this URL as a cache-busting identifier (the value changes
    whenever photo_file_id changes).
    """
    if profile is None or profile.photo_file_id is None:
        return None
    return f"/students/profile/photo?v={profile.photo_file_id}"


def _service(
    session: SessionDep,
    blobs: Annotated[BlobStore, Depends(get_blob_store)],
) -> StudentProfileService:
    return StudentProfileService(session, blobs)


StudentSvc = Annotated[StudentProfileService, Depends(_service)]
AiDep = Annotated[AIProvider, Depends(get_ai_provider)]


# ---- profile ----------------------------------------------------------


@router.get("/profile", response_model=StudentProfileRead | None)
async def get_profile(user: CurrentUser, svc: StudentSvc) -> StudentProfileRead | None:
    row = await svc.get_profile(user.id)
    if row is None:
        return None
    return _profile_to_read(row, photo_url=_photo_url_for(user.id, row))


@router.put("/profile", response_model=StudentProfileRead)
async def update_profile(
    payload: StudentProfileUpdate, user: CurrentUser, svc: StudentSvc
) -> StudentProfileRead:
    row = await svc.upsert_profile(user.id, payload)
    return _profile_to_read(row, photo_url=_photo_url_for(user.id, row))


# ---- photo ------------------------------------------------------------


@router.post("/profile/photo", response_model=StudentProfileRead)
async def upload_photo(
    user: CurrentUser,
    svc: StudentSvc,
    file: UploadFile = File(...),
) -> StudentProfileRead:
    if file.content_type not in ALLOWED_PHOTO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported photo type: {file.content_type}. Use JPEG, PNG, or WebP.",
        )
    content = await read_upload_limited(
        file,
        max_bytes=MAX_PHOTO_BYTES,
        detail=f"Photo too large (max {MAX_PHOTO_BYTES // (1024 * 1024)} MB)",
    )
    profile, _ = await svc.attach_photo(
        user_id=user.id,
        filename=file.filename or "photo",
        content_type=file.content_type or "image/jpeg",
        content=content,
    )
    return _profile_to_read(profile, photo_url=_photo_url_for(user.id, profile))


@router.get("/profile/photo")
async def get_photo(user: CurrentUser, svc: StudentSvc) -> Response:
    payload = await svc.get_photo(user.id)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No photo uploaded"
        )
    file_row, data = payload
    return Response(content=data, media_type=file_row.content_type)


# ---- entries ----------------------------------------------------------


@router.get("/entries", response_model=StudentEntryListResponse)
async def list_entries(user: CurrentUser, svc: StudentSvc) -> StudentEntryListResponse:
    rows = await svc.list_entries(user.id)
    return StudentEntryListResponse(items=[_entry_to_read(r) for r in rows])


@router.post(
    "/entries", response_model=StudentEntryRead, status_code=status.HTTP_201_CREATED
)
async def create_entry(
    payload: StudentEntryUpsert, user: CurrentUser, svc: StudentSvc
) -> StudentEntryRead:
    row = await svc.create_entry(user.id, payload)
    return _entry_to_read(row)


@router.put("/entries/{entry_id}", response_model=StudentEntryRead)
async def update_entry(
    entry_id: UUID,
    payload: StudentEntryUpsert,
    user: CurrentUser,
    svc: StudentSvc,
) -> StudentEntryRead:
    row = await svc.update_entry(user.id, entry_id, payload)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return _entry_to_read(row)


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: UUID, user: CurrentUser, svc: StudentSvc
) -> Response:
    ok = await svc.delete_entry(user.id, entry_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---- coaching ---------------------------------------------------------


@router.post("/coach/email", response_model=EmailCoachResponse)
async def coach_email(user: CurrentUser, payload: EmailCoachRequest) -> EmailCoachResponse:
    # Gated like every other /students route — the wizard is the only
    # caller and always sends a token. (This was the lone unauthenticated
    # /students endpoint; rule-based, but no reason to serve it anonymously.)
    return StudentCoachService.check_email(payload)


@router.post("/coach/photo", response_model=PhotoCoachResponse)
async def coach_photo(
    user: CurrentUser,
    ai: AiDep,
    file: UploadFile = File(...),
) -> PhotoCoachResponse:
    if file.content_type not in ALLOWED_PHOTO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported photo type: {file.content_type}.",
        )
    content = await read_upload_limited(
        file,
        max_bytes=MAX_PHOTO_BYTES,
        detail="Photo too large.",
    )
    coach = StudentCoachService(ai)
    start = time.perf_counter()
    try:
        result = await coach.check_photo(
            image_bytes=content, mime_type=file.content_type or "image/jpeg"
        )
    except Exception as exc:
        _emit(user.id, "coach.photo", start, error=str(exc), coach=coach)
        raise
    _emit(user.id, "coach.photo", start, coach=coach)
    return result


@router.post("/coach/text", response_model=TextCoachResponse)
async def coach_text(
    payload: TextCoachRequest, user: CurrentUser, ai: AiDep
) -> TextCoachResponse:
    coach = StudentCoachService(ai)
    start = time.perf_counter()
    try:
        result = await coach.improve_text(payload)
    except Exception as exc:
        _emit(user.id, "coach.text", start, error=str(exc), coach=coach)
        raise
    _emit(
        user.id,
        "coach.text",
        start,
        meta={"field": payload.field},
        coach=coach,
    )
    return result


@router.post("/coach/internship", response_model=InternshipCoachResponse)
async def coach_internship(
    payload: InternshipCoachRequest, user: CurrentUser, ai: AiDep
) -> InternshipCoachResponse:
    """Convert raw internship input into a professional summary + 2-4
    ATS bullets. If the input is too vague, returns follow-up questions
    instead of guessing.
    """
    coach = StudentCoachService(ai)
    start = time.perf_counter()
    try:
        result = await coach.improve_internship(payload)
    except Exception as exc:
        _emit(
            user.id,
            "coach.internship",
            start,
            error=str(exc),
            meta={"field": payload.field_},
            coach=coach,
        )
        raise
    _emit(
        user.id,
        "coach.internship",
        start,
        meta={
            "field": payload.field_,
            "vague": result.vague,
            "bullet_count": len(result.bullets),
        },
        coach=coach,
    )
    return result


@router.get("/coach/proofread", response_model=ProofreadResponse)
async def coach_proofread(
    user: CurrentUser, svc: StudentSvc, ai: AiDep
) -> ProofreadResponse:
    """Final proofreading pass over the whole CV.

    Called from the wizard's Preview step. Returns targeted fixes the
    student can apply or ignore, one at a time. Never blocks — an empty
    fixes list is a success.
    """
    profile, entries = await svc.load_profile_bundle(user.id)
    coach = StudentCoachService(ai)
    start = time.perf_counter()
    try:
        result = await coach.proofread(profile=profile, entries=entries)
    except Exception as exc:
        _emit(user.id, "coach.proofread", start, error=str(exc), coach=coach)
        raise
    _emit(
        user.id,
        "coach.proofread",
        start,
        meta={"fixes": len(result.fixes)},
        coach=coach,
    )
    return result


@router.get("/coach/draft-summary", response_model=DraftSummaryResponse)
async def coach_draft_summary(
    user: CurrentUser, svc: StudentSvc, ai: AiDep
) -> DraftSummaryResponse:
    """Draft a CV headline + summary from the student's collected info.

    Called from the wizard's Summary step (placed late in the wizard so the
    AI has skills / courses / projects to work from). Always advisory —
    the student can use it, edit it, or write their own.
    """
    profile, entries = await svc.load_profile_bundle(user.id)
    coach = StudentCoachService(ai)
    start = time.perf_counter()
    try:
        result = await coach.draft_summary(profile=profile, entries=entries)
    except Exception as exc:
        _emit(user.id, "coach.draft_summary", start, error=str(exc), coach=coach)
        raise
    _emit(user.id, "coach.draft_summary", start, coach=coach)
    return result


# ---- CV preview + PDF -------------------------------------------------


async def _load_photo(svc: StudentProfileService, user_id: UUID) -> tuple[bytes | None, str | None]:
    """Pre-fetch photo bytes from the active BlobStore for the renderer.

    Returns (bytes, mime) — both None when the student has no photo or
    when the blob is missing (the CV degrades gracefully and just leaves
    the photo slot blank).
    """
    payload = await svc.get_photo(user_id)
    if payload is None:
        return None, None
    file_row, data = payload
    return data, file_row.content_type


@router.get("/cv-templates", response_model=CvTemplateListResponse)
async def list_cv_templates(
    user: CurrentUser, svc: StudentSvc, session: SessionDep
) -> CvTemplateListResponse:
    """Visible templates for the picker + the slug that would render if
    the student clicked Download right now (resolved from their saved
    choice, falling back to the first visible)."""
    tmpl_svc = CvTemplateService(session)
    visible = await tmpl_svc.list_visible()
    profile = await svc.get_profile(user.id)
    default_slug = await tmpl_svc.resolve_slug(
        requested=None,
        profile_slug=profile.cv_template_slug if profile else None,
    )
    return CvTemplateListResponse(
        items=[CvTemplateRead.model_validate(t) for t in visible],
        default_slug=default_slug,
    )


@router.get("/cv/preview", response_model=CvPreviewResponse)
async def cv_preview(
    user: CurrentUser,
    svc: StudentSvc,
    session: SessionDep,
    template: str | None = Query(default=None, max_length=64),
) -> CvPreviewResponse:
    profile, entries = await svc.load_profile_bundle(user.id)
    photo_bytes, photo_mime = await _load_photo(svc, user.id)
    slug = await CvTemplateService(session).resolve_slug(
        requested=template,
        profile_slug=profile.cv_template_slug if profile else None,
    )
    renderer = StudentCvRenderer()
    html = renderer.render_html(
        profile=profile,
        entries=entries,
        photo_bytes=photo_bytes,
        photo_mime=photo_mime,
        template_slug=slug,
    )
    return CvPreviewResponse(html=html)


@router.get("/cv.pdf")
async def cv_pdf(
    user: CurrentUser,
    svc: StudentSvc,
    session: SessionDep,
    template: str | None = Query(default=None, max_length=64),
) -> Response:
    profile, entries = await svc.load_profile_bundle(user.id)
    photo_bytes, photo_mime = await _load_photo(svc, user.id)
    slug = await CvTemplateService(session).resolve_slug(
        requested=template,
        profile_slug=profile.cv_template_slug if profile else None,
    )
    renderer = StudentCvRenderer()
    start = time.perf_counter()
    try:
        pdf = renderer.render_pdf(
            profile=profile,
            entries=entries,
            photo_bytes=photo_bytes,
            photo_mime=photo_mime,
            template_slug=slug,
        )
    except WeasyPrintUnavailable as exc:
        _emit(user.id, "cv.pdf", start, error=str(exc), meta={"template": slug})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    filename = (profile.full_name if profile and profile.full_name else "cv").replace(
        " ", "_"
    )
    _emit(
        user.id,
        "cv.pdf",
        start,
        meta={"size_bytes": len(pdf), "template": slug},
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
    )


@router.get("/cv.docx")
async def cv_docx(
    user: CurrentUser,
    svc: StudentSvc,
    session: SessionDep,
    template: str | None = Query(default=None, max_length=64),
) -> Response:
    """Editable Word (.docx) export. Generated programmatically from
    the structured profile — no PDF-to-DOCX conversion. Single column,
    standard fonts, ATS-friendly.
    """
    profile, entries = await svc.load_profile_bundle(user.id)
    photo_bytes, photo_mime = await _load_photo(svc, user.id)
    slug = await CvTemplateService(session).resolve_slug(
        requested=template,
        profile_slug=profile.cv_template_slug if profile else None,
    )
    renderer = StudentCvDocxRenderer()
    start = time.perf_counter()
    try:
        docx_bytes = renderer.render_docx(
            profile=profile,
            entries=entries,
            photo_bytes=photo_bytes,
            photo_mime=photo_mime,
            template_slug=slug,
        )
    except Exception as exc:
        _emit(user.id, "cv.docx", start, error=str(exc), meta={"template": slug})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not build DOCX",
        ) from exc
    filename = (profile.full_name if profile and profile.full_name else "cv").replace(
        " ", "_"
    )
    _emit(
        user.id,
        "cv.docx",
        start,
        meta={"size_bytes": len(docx_bytes), "template": slug},
    )
    return Response(
        content=docx_bytes,
        media_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}_CV.docx"',
        },
    )


# ---- feedback + post-download survey ----------------------------------


def _feedback_service(
    session: SessionDep,
    email_provider: Annotated[EmailProvider, Depends(get_email_provider)],
    blobs: Annotated[BlobStore, Depends(get_blob_store)],
) -> FeedbackService:
    return FeedbackService(session, email_provider, blobs)


FeedbackSvc = Annotated[FeedbackService, Depends(_feedback_service)]


@router.post("/feedback", response_model=FeedbackRead)
async def submit_feedback(
    user: CurrentUser,
    svc: FeedbackSvc,
    message: Annotated[str, Form()],
    screenshot: Annotated[UploadFile | None, File()] = None,
) -> FeedbackRead:
    """Submit general feedback with an optional screenshot.

    Multipart form: `message` (required) + `screenshot` (optional image).
    Message is trimmed first, then length-checked, so a whitespace-only
    body is rejected. The screenshot is validated (type + size) here and
    handed to the service as raw bytes to store.
    """
    cleaned = message.strip()
    if not (FEEDBACK_MESSAGE_MIN_LEN <= len(cleaned) <= FEEDBACK_MESSAGE_MAX_LEN):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Feedback must be between {FEEDBACK_MESSAGE_MIN_LEN} and "
                f"{FEEDBACK_MESSAGE_MAX_LEN} characters."
            ),
        )

    screenshot_upload = None
    if screenshot is not None and screenshot.filename:
        if screenshot.content_type not in ALLOWED_SCREENSHOT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=(
                    f"Unsupported screenshot type: {screenshot.content_type}. "
                    "Use PNG, JPEG, or WebP."
                ),
            )
        content = await read_upload_limited(
            screenshot,
            max_bytes=MAX_SCREENSHOT_BYTES,
            detail=f"Screenshot too large (max {MAX_SCREENSHOT_BYTES // (1024 * 1024)} MB)",
        )
        screenshot_upload = (
            screenshot.filename,
            screenshot.content_type or "image/png",
            content,
        )

    row = await svc.submit_general(user.id, cleaned, screenshot=screenshot_upload)
    return FeedbackRead.model_validate(row)


@router.post("/survey", response_model=FeedbackRead)
async def submit_survey(
    payload: SurveyCreate,
    user: CurrentUser,
    svc: FeedbackSvc,
) -> FeedbackRead:
    row = await svc.submit_survey(
        user.id,
        rating=payload.rating,
        comment=payload.comment,
        template_slug=payload.template_slug,
    )
    return FeedbackRead.model_validate(row)
