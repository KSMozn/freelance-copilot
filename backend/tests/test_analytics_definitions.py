"""Outcome-definition predicates — the contract for everything downstream."""
from datetime import UTC, datetime

from app.domain.analytics.definitions import (
    is_active,
    is_completed,
    is_interviewed,
    is_lost,
    is_won,
)
from app.domain.entities.application import ApplicationStatus
from tests.factories import make_application


def test_active_includes_applied_viewed_interview_offer() -> None:
    for s in (
        ApplicationStatus.applied,
        ApplicationStatus.viewed,
        ApplicationStatus.interview,
        ApplicationStatus.offer,
    ):
        assert is_active(make_application(status=s))


def test_active_excludes_terminals_and_draft() -> None:
    for s in (
        ApplicationStatus.draft,
        ApplicationStatus.won,
        ApplicationStatus.completed,
        ApplicationStatus.rejected,
        ApplicationStatus.withdrawn,
    ):
        assert not is_active(make_application(status=s))


def test_interviewed_is_inclusive_through_won_completed() -> None:
    for s in (
        ApplicationStatus.interview,
        ApplicationStatus.offer,
        ApplicationStatus.won,
        ApplicationStatus.completed,
    ):
        assert is_interviewed(make_application(status=s))


def test_interviewed_via_explicit_timestamp() -> None:
    # An application that's now rejected but had an interview earlier
    # should still count as interviewed for funnel math.
    rejected_with_interview = make_application(
        status=ApplicationStatus.rejected,
        interview_at=datetime.now(UTC),
    )
    assert is_interviewed(rejected_with_interview)


def test_interviewed_excludes_pre_interview_states() -> None:
    for s in (ApplicationStatus.applied, ApplicationStatus.viewed, ApplicationStatus.draft):
        app = make_application(status=s)
        assert not is_interviewed(app)


def test_won_and_completed_definitions() -> None:
    assert is_won(make_application(status=ApplicationStatus.won))
    assert is_won(make_application(status=ApplicationStatus.completed))
    assert not is_won(make_application(status=ApplicationStatus.offer))
    assert is_completed(make_application(status=ApplicationStatus.completed))
    assert not is_completed(make_application(status=ApplicationStatus.won))


def test_lost_definitions() -> None:
    assert is_lost(make_application(status=ApplicationStatus.rejected))
    assert is_lost(make_application(status=ApplicationStatus.withdrawn))
    assert not is_lost(make_application(status=ApplicationStatus.completed))
