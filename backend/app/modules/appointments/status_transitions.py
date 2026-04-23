"""Allowed AppointmentStatus transitions (T12.7).

Port of `ops:lib/job_tracker._check_status` adapted from string statuses
to `AppointmentStatus` enum values. Every CRUD update that changes
status must go through `check_transition()`; terminal states have no
outgoing edges.

Matrix:
    SCHEDULED  → ATTENDED, MISSED, CANCELLED, RESCHEDULED
    RESCHEDULED → ATTENDED, MISSED, CANCELLED
    ATTENDED / MISSED / CANCELLED → (terminal; no transitions)
"""

from __future__ import annotations

from app.modules.common.temporal_types import AppointmentStatus

ALLOWED: dict[AppointmentStatus, set[AppointmentStatus]] = {
    AppointmentStatus.SCHEDULED: {
        AppointmentStatus.ATTENDED,
        AppointmentStatus.MISSED,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.RESCHEDULED,
    },
    AppointmentStatus.ATTENDED: set(),
    AppointmentStatus.MISSED: set(),
    AppointmentStatus.CANCELLED: set(),
    AppointmentStatus.RESCHEDULED: {
        AppointmentStatus.ATTENDED,
        AppointmentStatus.MISSED,
        AppointmentStatus.CANCELLED,
    },
}


class InvalidStatusTransition(ValueError):
    """Raised when a status update violates the ALLOWED matrix."""


def check_transition(
    current: AppointmentStatus, target: AppointmentStatus
) -> None:
    """Raise InvalidStatusTransition if `current → target` is not allowed.

    No-op transitions (current == target) are rejected — callers should
    only invoke this when the status is actually changing.
    """
    if target not in ALLOWED.get(current, set()):
        raise InvalidStatusTransition(
            f"cannot transition appointment from {current.value!r} "
            f"to {target.value!r}"
        )


__all__ = ["ALLOWED", "InvalidStatusTransition", "check_transition"]
