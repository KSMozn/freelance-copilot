"""Career Starter Pack endpoints — LinkedIn / GitHub content generation.

Mounted under `/students/career-pack`. All routes are authenticated and
scoped to the current student's own profile. See CareerPackService for
the safety guarantees (no scraping, no auth to LinkedIn, only public
GitHub API).
"""
from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.application.dto.career_pack_dto import (
    CareerPackRead,
    ClearRequest,
    GitHubGenerated,
    GitHubReview,
    GitHubReviewRequest,
    LinkedInGenerated,
    LinkedInReview,
)
from app.application.services import usage_event_service
from app.application.services.career_pack_service import (
    CareerPackError,
    CareerPackService,
)
from app.application.services.student_profile_service import StudentProfileService
from app.application.services.text_extraction import (
    TextExtractionError,
    extract_text,
)
from app.core.deps import (
    CurrentUser,
    SessionDep,
    get_ai_provider,
    get_blob_store,
)
from app.domain.providers.ai_provider import AIProvider
from app.domain.providers.blob_store import BlobStore

router = APIRouter(prefix="/students/career-pack", tags=["student", "career-pack"])


def _student_svc(session: SessionDep, blobs: Annotated[BlobStore, Depends(get_blob_store)]) -> StudentProfileService:
    return StudentProfileService(session, blobs)


StudentSvc = Annotated[StudentProfileService, Depends(_student_svc)]
AiDep = Annotated[AIProvider, Depends(get_ai_provider)]


def _emit(user_id, name: str, start: float, meta=None, error=None) -> None:
    latency_ms = int((time.perf_counter() - start) * 1000)
    usage_event_service.fire(
        user_id=user_id,
        kind=name,
        status="error" if error else "ok",
        duration_ms=latency_ms,
        error_message=error,
        meta=meta or {},
    )


def _svc(session: SessionDep, ai: AiDep) -> CareerPackService:
    return CareerPackService(session=session, ai_provider=ai)


CareerSvc = Annotated[CareerPackService, Depends(_svc)]


@router.get("", response_model=CareerPackRead)
async def read_career_pack(
    user: CurrentUser, student: StudentSvc, career: CareerSvc
) -> CareerPackRead:
    profile = await student.get_profile(user.id)
    return career.read(profile)


@router.post("/linkedin/generate", response_model=LinkedInGenerated)
async def generate_linkedin(
    user: CurrentUser, student: StudentSvc, career: CareerSvc
) -> LinkedInGenerated:
    profile, entries = await student.load_profile_bundle(user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fill in your CV basics first, then we can generate LinkedIn content.",
        )
    start = time.perf_counter()
    try:
        result = await career.generate_linkedin(profile=profile, entries=entries)
    except CareerPackError as exc:
        _emit(user.id, "career_pack.linkedin.generate", start, error=str(exc))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    _emit(user.id, "career_pack.linkedin.generate", start)
    return result


@router.post("/linkedin/review", response_model=LinkedInReview)
async def review_linkedin(
    user: CurrentUser,
    student: StudentSvc,
    career: CareerSvc,
    linkedin_url: Annotated[str, Form(min_length=10, max_length=300)],
    file: Annotated[UploadFile, File(description="LinkedIn PDF export")],
) -> LinkedInReview:
    """Review the student's LinkedIn against their CV.

    Takes the LinkedIn URL (for record) plus the student's exported LinkedIn
    PDF (LinkedIn → Me → Save to PDF). Careero extracts the text server-side
    and compares against the CV — no scraping, no LinkedIn auth required.
    """
    profile, entries = await student.load_profile_bundle(user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fill in your CV basics first.",
        )
    content = await file.read()
    try:
        profile_text = extract_text(
            content=content, content_type=file.content_type or ""
        )
    except TextExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    start = time.perf_counter()
    try:
        result = await career.review_linkedin(
            profile=profile,
            entries=entries,
            linkedin_url=linkedin_url,
            profile_text=profile_text,
        )
    except CareerPackError as exc:
        _emit(user.id, "career_pack.linkedin.review", start, error=str(exc))
        code = (
            status.HTTP_400_BAD_REQUEST
            if "doesn't look like" in str(exc) or "Add a few CV details" in str(exc)
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    _emit(user.id, "career_pack.linkedin.review", start)
    return result


@router.post("/github/generate", response_model=GitHubGenerated)
async def generate_github(
    user: CurrentUser, student: StudentSvc, career: CareerSvc
) -> GitHubGenerated:
    profile, entries = await student.load_profile_bundle(user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fill in your CV basics first, then we can generate GitHub content.",
        )
    start = time.perf_counter()
    try:
        result = await career.generate_github(profile=profile, entries=entries)
    except CareerPackError as exc:
        _emit(user.id, "career_pack.github.generate", start, error=str(exc))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    _emit(user.id, "career_pack.github.generate", start)
    return result


@router.post("/clear", response_model=CareerPackRead)
async def clear_career_pack(
    payload: ClearRequest,
    user: CurrentUser,
    student: StudentSvc,
    career: CareerSvc,
) -> CareerPackRead:
    profile = await student.get_profile(user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fill in your CV basics first.",
        )
    await career.clear(profile=profile, side=payload.side, kind=payload.kind)
    return career.read(profile)


@router.post("/github/review", response_model=GitHubReview)
async def review_github(
    payload: GitHubReviewRequest,
    user: CurrentUser,
    student: StudentSvc,
    career: CareerSvc,
) -> GitHubReview:
    profile, entries = await student.load_profile_bundle(user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fill in your CV basics first.",
        )
    start = time.perf_counter()
    try:
        result = await career.review_github(
            profile=profile,
            entries=entries,
            identifier=payload.identifier,
        )
    except CareerPackError as exc:
        _emit(user.id, "career_pack.github.review", start, error=str(exc))
        # 400 for bad usernames / no-such-user; 502 for AI upstream flakes.
        code = (
            status.HTTP_400_BAD_REQUEST
            if "Invalid GitHub username" in str(exc) or "No public GitHub" in str(exc)
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    _emit(user.id, "career_pack.github.review", start)
    return result
