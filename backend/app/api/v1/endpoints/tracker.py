"""Application tracker endpoints (Phase H).

One nested router per application — each application gets its own
recruiter interactions, interview events, and follow-up reminders.
There's also a top-level ``GET /tracker/reminders`` for the dashboard's
"open follow-ups" widget.
"""
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.application.dto.tracker_dto import (
    ApplicationActivityRead,
    FollowUpReminderCreate,
    FollowUpReminderRead,
    InterviewEventCreate,
    InterviewEventRead,
    InterviewEventUpdate,
    RecruiterInteractionCreate,
    RecruiterInteractionRead,
)
from app.core.deps import CurrentUser, SessionDep
from app.infrastructure.db.repositories.sqlalchemy_application_repository import (
    SQLAlchemyApplicationRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_tracker_repositories import (
    SQLAlchemyFollowUpReminderRepository,
    SQLAlchemyInterviewEventRepository,
    SQLAlchemyRecruiterInteractionRepository,
)

# Two routers — nested per-application, and a flat "my reminders" view.
application_tracker_router = APIRouter(
    prefix="/applications/{application_id}", tags=["tracker"]
)
tracker_router = APIRouter(prefix="/tracker", tags=["tracker"])


async def _verify_application(
    *, session, user_id: UUID, application_id: UUID
) -> None:
    """Refuse if the application doesn't belong to the current user."""
    repo = SQLAlchemyApplicationRepository(session)
    app = await repo.get_by_id(user_id=user_id, application_id=application_id)
    if app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
        )


# ---- Application activity bundle ----------------------------------------


@application_tracker_router.get("/activity", response_model=ApplicationActivityRead)
async def get_application_activity(
    application_id: UUID,
    user: CurrentUser,
    session: SessionDep,
) -> ApplicationActivityRead:
    await _verify_application(session=session, user_id=user.id, application_id=application_id)
    interactions_repo = SQLAlchemyRecruiterInteractionRepository(session)
    interviews_repo = SQLAlchemyInterviewEventRepository(session)
    reminders_repo = SQLAlchemyFollowUpReminderRepository(session)

    interactions = await interactions_repo.list_for_application(
        user_id=user.id, application_id=application_id
    )
    interviews = await interviews_repo.list_for_application(
        user_id=user.id, application_id=application_id
    )
    reminders = await reminders_repo.list_for_application(
        user_id=user.id, application_id=application_id
    )
    return ApplicationActivityRead(
        interactions=[RecruiterInteractionRead.model_validate(i) for i in interactions],
        interviews=[InterviewEventRead.model_validate(i) for i in interviews],
        reminders=[FollowUpReminderRead.model_validate(r) for r in reminders],
    )


# ---- Recruiter interactions ---------------------------------------------


@application_tracker_router.post(
    "/interactions",
    response_model=RecruiterInteractionRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_interaction(
    application_id: UUID,
    payload: RecruiterInteractionCreate,
    user: CurrentUser,
    session: SessionDep,
) -> RecruiterInteractionRead:
    await _verify_application(session=session, user_id=user.id, application_id=application_id)
    repo = SQLAlchemyRecruiterInteractionRepository(session)
    row = await repo.create(
        user_id=user.id,
        application_id=application_id,
        channel=payload.channel,
        direction=payload.direction,
        occurred_at=payload.occurred_at,
        contact_name=payload.contact_name,
        summary=payload.summary,
        raw_content=payload.raw_content,
    )
    return RecruiterInteractionRead.model_validate(row)


@application_tracker_router.delete(
    "/interactions/{interaction_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_interaction(
    application_id: UUID,
    interaction_id: UUID,
    user: CurrentUser,
    session: SessionDep,
) -> None:
    await _verify_application(session=session, user_id=user.id, application_id=application_id)
    repo = SQLAlchemyRecruiterInteractionRepository(session)
    if not await repo.delete(user_id=user.id, interaction_id=interaction_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found"
        )


# ---- Interview events ----------------------------------------------------


@application_tracker_router.post(
    "/interviews",
    response_model=InterviewEventRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_interview(
    application_id: UUID,
    payload: InterviewEventCreate,
    user: CurrentUser,
    session: SessionDep,
) -> InterviewEventRead:
    await _verify_application(session=session, user_id=user.id, application_id=application_id)
    repo = SQLAlchemyInterviewEventRepository(session)
    row = await repo.create(
        user_id=user.id,
        application_id=application_id,
        round_label=payload.round_label,
        format=payload.format,
        scheduled_at=payload.scheduled_at,
        duration_minutes=payload.duration_minutes,
        interviewer_names=payload.interviewer_names,
    )
    return InterviewEventRead.model_validate(row)


@application_tracker_router.patch(
    "/interviews/{event_id}", response_model=InterviewEventRead
)
async def update_interview(
    application_id: UUID,
    event_id: UUID,
    payload: InterviewEventUpdate,
    user: CurrentUser,
    session: SessionDep,
) -> InterviewEventRead:
    await _verify_application(session=session, user_id=user.id, application_id=application_id)
    repo = SQLAlchemyInterviewEventRepository(session)
    row = await repo.update(
        user_id=user.id,
        event_id=event_id,
        patch=payload.model_dump(exclude_unset=True),
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Interview event not found"
        )
    return InterviewEventRead.model_validate(row)


@application_tracker_router.delete(
    "/interviews/{event_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_interview(
    application_id: UUID,
    event_id: UUID,
    user: CurrentUser,
    session: SessionDep,
) -> None:
    await _verify_application(session=session, user_id=user.id, application_id=application_id)
    repo = SQLAlchemyInterviewEventRepository(session)
    if not await repo.delete(user_id=user.id, event_id=event_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Interview event not found"
        )


# ---- Follow-up reminders -------------------------------------------------


@application_tracker_router.post(
    "/reminders",
    response_model=FollowUpReminderRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_reminder(
    application_id: UUID,
    payload: FollowUpReminderCreate,
    user: CurrentUser,
    session: SessionDep,
) -> FollowUpReminderRead:
    await _verify_application(session=session, user_id=user.id, application_id=application_id)
    repo = SQLAlchemyFollowUpReminderRepository(session)
    row = await repo.create(
        user_id=user.id,
        application_id=application_id,
        due_at=payload.due_at,
        note=payload.note,
        channel=payload.channel,
    )
    return FollowUpReminderRead.model_validate(row)


@application_tracker_router.post(
    "/reminders/{reminder_id}/complete", response_model=FollowUpReminderRead
)
async def complete_reminder(
    application_id: UUID,
    reminder_id: UUID,
    user: CurrentUser,
    session: SessionDep,
) -> FollowUpReminderRead:
    await _verify_application(session=session, user_id=user.id, application_id=application_id)
    repo = SQLAlchemyFollowUpReminderRepository(session)
    row = await repo.mark_complete(
        user_id=user.id,
        reminder_id=reminder_id,
        completed_at=datetime.now(UTC),
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found"
        )
    return FollowUpReminderRead.model_validate(row)


@application_tracker_router.delete(
    "/reminders/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_reminder(
    application_id: UUID,
    reminder_id: UUID,
    user: CurrentUser,
    session: SessionDep,
) -> None:
    await _verify_application(session=session, user_id=user.id, application_id=application_id)
    repo = SQLAlchemyFollowUpReminderRepository(session)
    if not await repo.delete(user_id=user.id, reminder_id=reminder_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found"
        )


# ---- Top-level: dashboard "open reminders" ------------------------------


@tracker_router.get("/reminders", response_model=list[FollowUpReminderRead])
async def list_open_reminders(
    user: CurrentUser,
    session: SessionDep,
    limit: int = 50,
) -> list[FollowUpReminderRead]:
    repo = SQLAlchemyFollowUpReminderRepository(session)
    rows = await repo.list_open_for_user(user_id=user.id, limit=limit)
    return [FollowUpReminderRead.model_validate(r) for r in rows]
