"""Canonical outcome definitions for analytics.

The whole codebase agrees on what "interviewed", "won", and "lost" mean here.
Centralizing the predicates keeps the dashboard, future learning loop, and
any CLI exports from drifting apart.

`interviewed` is **inclusive**: an application that progressed all the way to
"won" was also interviewed. That's the right semantics for funnel rates.
"""
from __future__ import annotations

from app.domain.entities.application import Application, ApplicationStatus

INTERVIEW_STATUSES: frozenset[ApplicationStatus] = frozenset(
    {
        ApplicationStatus.interview,
        ApplicationStatus.offer,
        ApplicationStatus.won,
        ApplicationStatus.completed,
    }
)

WON_STATUSES: frozenset[ApplicationStatus] = frozenset(
    {ApplicationStatus.won, ApplicationStatus.completed}
)

COMPLETED_STATUSES: frozenset[ApplicationStatus] = frozenset(
    {ApplicationStatus.completed}
)

LOST_STATUSES: frozenset[ApplicationStatus] = frozenset(
    {ApplicationStatus.rejected, ApplicationStatus.withdrawn}
)

ACTIVE_STATUSES: frozenset[ApplicationStatus] = frozenset(
    {
        ApplicationStatus.applied,
        ApplicationStatus.viewed,
        ApplicationStatus.interview,
        ApplicationStatus.offer,
    }
)


def is_interviewed(app: Application) -> bool:
    """True if the application progressed to interview or beyond OR has an
    explicit `interview_at` timestamp (e.g. recorded retroactively).
    """
    return app.status in INTERVIEW_STATUSES or app.interview_at is not None


def is_won(app: Application) -> bool:
    return app.status in WON_STATUSES


def is_completed(app: Application) -> bool:
    return app.status in COMPLETED_STATUSES


def is_lost(app: Application) -> bool:
    return app.status in LOST_STATUSES


def is_active(app: Application) -> bool:
    return app.status in ACTIVE_STATUSES
