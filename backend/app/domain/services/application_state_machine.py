"""Pure status state-machine for applications.

Stays in the domain layer because it encodes business rules — no IO, no
framework deps. Two helpers:

- `validate_transition(from_status, to_status)` raises `InvalidTransitionError`
  if the move isn't allowed. Same-status "transitions" are also rejected so
  callers can't accidentally double-write history rows.
- `allowed_next_statuses(from_status)` returns the set the UI can show.
"""
from __future__ import annotations

from app.domain.entities.application import ApplicationStatus
from app.domain.exceptions import DomainError

_TRANSITIONS: dict[ApplicationStatus, frozenset[ApplicationStatus]] = {
    ApplicationStatus.draft: frozenset({ApplicationStatus.applied}),
    ApplicationStatus.applied: frozenset(
        {
            ApplicationStatus.viewed,
            ApplicationStatus.interview,
            ApplicationStatus.rejected,
            ApplicationStatus.withdrawn,
        }
    ),
    ApplicationStatus.viewed: frozenset(
        {
            ApplicationStatus.interview,
            ApplicationStatus.rejected,
            ApplicationStatus.withdrawn,
        }
    ),
    ApplicationStatus.interview: frozenset(
        {
            ApplicationStatus.offer,
            ApplicationStatus.rejected,
            ApplicationStatus.withdrawn,
        }
    ),
    ApplicationStatus.offer: frozenset(
        {
            ApplicationStatus.won,
            ApplicationStatus.rejected,
            ApplicationStatus.withdrawn,
        }
    ),
    ApplicationStatus.won: frozenset({ApplicationStatus.completed}),
    # terminal:
    ApplicationStatus.rejected: frozenset(),
    ApplicationStatus.withdrawn: frozenset(),
    ApplicationStatus.completed: frozenset(),
}


class InvalidTransitionError(DomainError):
    pass


def allowed_next_statuses(status: ApplicationStatus) -> frozenset[ApplicationStatus]:
    return _TRANSITIONS.get(status, frozenset())


def validate_transition(
    *, from_status: ApplicationStatus, to_status: ApplicationStatus
) -> None:
    if from_status == to_status:
        raise InvalidTransitionError(
            f"Application is already in status '{from_status}'."
        )
    allowed = _TRANSITIONS.get(from_status, frozenset())
    if to_status not in allowed:
        allowed_str = ", ".join(sorted(s.value for s in allowed)) or "(none — terminal)"
        raise InvalidTransitionError(
            f"Cannot transition from '{from_status}' to '{to_status}'. "
            f"Allowed: {allowed_str}."
        )
