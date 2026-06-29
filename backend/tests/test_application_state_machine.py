import pytest

from app.domain.entities.application import TERMINAL_STATUSES, ApplicationStatus
from app.domain.services.application_state_machine import (
    InvalidTransitionError,
    allowed_next_statuses,
    validate_transition,
)

VALID_TRANSITIONS = [
    (ApplicationStatus.draft, ApplicationStatus.applied),
    (ApplicationStatus.applied, ApplicationStatus.viewed),
    (ApplicationStatus.applied, ApplicationStatus.interview),
    (ApplicationStatus.applied, ApplicationStatus.rejected),
    (ApplicationStatus.applied, ApplicationStatus.withdrawn),
    (ApplicationStatus.viewed, ApplicationStatus.interview),
    (ApplicationStatus.viewed, ApplicationStatus.rejected),
    (ApplicationStatus.viewed, ApplicationStatus.withdrawn),
    (ApplicationStatus.interview, ApplicationStatus.offer),
    (ApplicationStatus.interview, ApplicationStatus.rejected),
    (ApplicationStatus.interview, ApplicationStatus.withdrawn),
    (ApplicationStatus.offer, ApplicationStatus.won),
    (ApplicationStatus.offer, ApplicationStatus.rejected),
    (ApplicationStatus.offer, ApplicationStatus.withdrawn),
    (ApplicationStatus.won, ApplicationStatus.completed),
]


INVALID_TRANSITIONS = [
    (ApplicationStatus.applied, ApplicationStatus.offer),
    (ApplicationStatus.applied, ApplicationStatus.won),
    (ApplicationStatus.viewed, ApplicationStatus.offer),
    (ApplicationStatus.draft, ApplicationStatus.interview),
    (ApplicationStatus.completed, ApplicationStatus.won),
    (ApplicationStatus.rejected, ApplicationStatus.applied),
    (ApplicationStatus.withdrawn, ApplicationStatus.applied),
]


@pytest.mark.parametrize("frm,to", VALID_TRANSITIONS)
def test_valid_transition(frm, to) -> None:  # type: ignore[no-untyped-def]
    validate_transition(from_status=frm, to_status=to)


@pytest.mark.parametrize("frm,to", INVALID_TRANSITIONS)
def test_invalid_transition_raises(frm, to) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(InvalidTransitionError):
        validate_transition(from_status=frm, to_status=to)


def test_self_transition_is_rejected() -> None:
    with pytest.raises(InvalidTransitionError):
        validate_transition(
            from_status=ApplicationStatus.applied, to_status=ApplicationStatus.applied
        )


def test_terminal_statuses_have_no_allowed_next() -> None:
    for terminal in (
        ApplicationStatus.rejected,
        ApplicationStatus.withdrawn,
        ApplicationStatus.completed,
    ):
        assert allowed_next_statuses(terminal) == frozenset()


def test_terminal_set_matches_spec() -> None:
    assert TERMINAL_STATUSES == frozenset(
        {
            ApplicationStatus.rejected,
            ApplicationStatus.withdrawn,
            ApplicationStatus.completed,
        }
    )
