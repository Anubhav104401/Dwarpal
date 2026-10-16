"""The life of a verification session, as a small state machine that allows only legal moves."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from dwarpal_api.domain.decision import Outcome


class Status(StrEnum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    AWAITING_STEP_UP = "awaiting_step_up"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELED = "canceled"


ALLOWED: dict[Status, frozenset[Status]] = {
    Status.CREATED: frozenset({Status.IN_PROGRESS, Status.EXPIRED, Status.CANCELED}),
    Status.IN_PROGRESS: frozenset(
        {Status.IN_PROGRESS, Status.AWAITING_STEP_UP, Status.COMPLETED, Status.EXPIRED, Status.CANCELED}
    ),
    Status.AWAITING_STEP_UP: frozenset({Status.COMPLETED, Status.EXPIRED, Status.CANCELED}),
    Status.COMPLETED: frozenset(),
    Status.EXPIRED: frozenset(),
    Status.CANCELED: frozenset(),
}
OPEN = frozenset({Status.CREATED, Status.IN_PROGRESS, Status.AWAITING_STEP_UP})
STATUS_AFTER: dict[Outcome, Status] = {
    Outcome.PASS: Status.COMPLETED,
    Outcome.FAIL: Status.COMPLETED,
    Outcome.REJECT: Status.COMPLETED,
    Outcome.STEP_UP: Status.AWAITING_STEP_UP,
    Outcome.RETRY: Status.IN_PROGRESS,
}


class IllegalTransitionError(ValueError):
    """A move the state machine does not allow, such as reopening a completed session."""


def move(current: Status, target: Status) -> Status:
    if target not in ALLOWED[current]:
        raise IllegalTransitionError(f"a session cannot go from {current} to {target}")
    return target


def is_expired(status: Status, expires_at: datetime, now: datetime) -> bool:
    return status in OPEN and now >= expires_at
