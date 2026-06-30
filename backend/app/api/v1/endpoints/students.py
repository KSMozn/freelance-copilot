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

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from app.application.dto.student_dto import (
    CvPreviewResponse,
    DraftSummaryResponse,
    EmailCoachRequest,
    EmailCoachResponse,
    PhotoCoachResponse,
    StudentEntryListResponse,
    StudentEntryRead,
    StudentEntryUpsert,
    StudentProfileRead,
    StudentProfileUpdate,
    TextCoachRequest,
    TextCoachResponse,
)
from app.application.services.student_coach_service import StudentCoachService
from app.application.services.student_cv_renderer import (
    StudentCvRenderer,
    WeasyPrintUnavailable,
)
from app.application.services.student_profile_service import StudentProfileService
from app.core.deps import CurrentUser, SessionDep, get_ai_provider, get_blob_store
from app.domain.providers.ai_provider import AIProvider
from app.domain.providers.blob_store import BlobStore
from app.infrastructure.db.models.student_profile import (
    StudentProfile,
    StudentProfileEntry,
)

router = APIRouter(prefix="/students", tags=["student"])

MAX_PHOTO_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}


def _profile_to_read(row: StudentProfile, *, photo_url: str | None) -> StudentProfileRead:
    return StudentProfileRead(
        user_id=row.user_id,
        full_name=row.full_name,
        professional_email=row.professional_email,
        phone=row.phone,
        location=row.location,
        college=row.college,
        department=row.department,
        degree=row.degree,
        major=row.major,
        graduation_year=row.graduation_year,
        gpa=row.gpa,
        photo_file_id=row.photo_file_id,
        photo_url=photo_url,
        summary=row.summary,
        headline=row.headline,
        links=dict(row.links or {}),
        interests=list(row.interests or []),
        completed_steps=list(row.completed_steps or []),
        current_step=row.current_step,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _entry_to_read(row: StudentProfileEntry) -> StudentEntryRead:
    return StudentEntryRead(
        id=row.id,
        kind=row.kind,  # type: ignore[arg-type]
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
    content = await file.read()
    if len(content) > MAX_PHOTO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
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
async def coach_email(payload: EmailCoachRequest) -> EmailCoachResponse:
    return StudentCoachService.check_email(payload)


@router.post("/coach/photo", response_model=PhotoCoachResponse)
async def coach_photo(
    ai: AiDep,
    file: UploadFile = File(...),
) -> PhotoCoachResponse:
    if file.content_type not in ALLOWED_PHOTO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported photo type: {file.content_type}.",
        )
    content = await file.read()
    if len(content) > MAX_PHOTO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Photo too large.",
        )
    coach = StudentCoachService(ai)
    return await coach.check_photo(
        image_bytes=content, mime_type=file.content_type or "image/jpeg"
    )


@router.post("/coach/text", response_model=TextCoachResponse)
async def coach_text(payload: TextCoachRequest, ai: AiDep) -> TextCoachResponse:
    coach = StudentCoachService(ai)
    return await coach.improve_text(payload)


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
    return await coach.draft_summary(profile=profile, entries=entries)


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


@router.get("/cv/preview", response_model=CvPreviewResponse)
async def cv_preview(user: CurrentUser, svc: StudentSvc) -> CvPreviewResponse:
    profile, entries = await svc.load_profile_bundle(user.id)
    photo_bytes, photo_mime = await _load_photo(svc, user.id)
    renderer = StudentCvRenderer()
    html = renderer.render_html(
        profile=profile,
        entries=entries,
        photo_bytes=photo_bytes,
        photo_mime=photo_mime,
    )
    return CvPreviewResponse(html=html)


@router.get("/cv.pdf")
async def cv_pdf(user: CurrentUser, svc: StudentSvc) -> Response:
    profile, entries = await svc.load_profile_bundle(user.id)
    photo_bytes, photo_mime = await _load_photo(svc, user.id)
    renderer = StudentCvRenderer()
    try:
        pdf = renderer.render_pdf(
            profile=profile,
            entries=entries,
            photo_bytes=photo_bytes,
            photo_mime=photo_mime,
        )
    except WeasyPrintUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    filename = (profile.full_name if profile and profile.full_name else "cv").replace(
        " ", "_"
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
    )
