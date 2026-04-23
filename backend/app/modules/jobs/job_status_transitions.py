"""Allowed JobApplicationStatus transitions (T12.11).

Port of `ops:lib/job_tracker._check_status` adapted from string statuses
to `JobApplicationStatus` enum values. Every lifecycle update must go
through `check_transition()`; terminal states have no outgoing edges.

Matrix:
    DRAFT      → APPLIED, WITHDRAWN
    APPLIED    → INTERVIEW, REJECTED, WITHDRAWN
    INTERVIEW  → OFFER, REJECTED, WITHDRAWN
    OFFER      → REJECTED, WITHDRAWN      (accepting an offer is an end-state;
                                            no ACCEPTED value in the enum)
    REJECTED   → (terminal; no transitions)
    WITHDRAWN  → (terminal; no transitions)
"""

from __future__ import annotations

from app.modules.common.temporal_types import JobApplicationStatus

ALLOWED: dict[JobApplicationStatus, set[JobApplicationStatus]] = {
    JobApplicationStatus.DRAFT: {
        JobApplicationStatus.APPLIED,
        JobApplicationStatus.WITHDRAWN,
    },
    JobApplicationStatus.APPLIED: {
        JobApplicationStatus.INTERVIEW,
        JobApplicationStatus.REJECTED,
        JobApplicationStatus.WITHDRAWN,
    },
    JobApplicationStatus.INTERVIEW: {
        JobApplicationStatus.OFFER,
        JobApplicationStatus.REJECTED,
        JobApplicationStatus.WITHDRAWN,
    },
    JobApplicationStatus.OFFER: {
        JobApplicationStatus.REJECTED,
        JobApplicationStatus.WITHDRAWN,
    },
    JobApplicationStatus.REJECTED: set(),
    JobApplicationStatus.WITHDRAWN: set(),
}


class InvalidJobStatusTransition(ValueError):
    """Raised when a status update violates the ALLOWED matrix."""


def check_transition(
    current: JobApplicationStatus, target: JobApplicationStatus,
) -> None:
    """Raise InvalidJobStatusTransition if `current → target` is disallowed.

    No-op transitions (current == target) are rejected — callers should
    only invoke this when the status is actually changing.
    """
    if target not in ALLOWED.get(current, set()):
        raise InvalidJobStatusTransition(
            f"cannot transition job application from {current.value!r} "
            f"to {target.value!r}"
        )


__all__ = ["ALLOWED", "InvalidJobStatusTransition", "check_transition"]
