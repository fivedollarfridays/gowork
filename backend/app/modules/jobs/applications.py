"""Job application CRUD with status-machine validation + event emission (T12.11).

Public surface:
    create, get, update_status, list_by_session, list_by_status.

Persistence is delegated to `persistence.py`; transition rules live in
`job_status_transitions.py`. Every state-changing operation ends with
an `events.emit(...)` call — this module never imports its consumers,
keeping the coupling one-way (pub/sub layering).

Composite match linkage
-----------------------
`matching.JobMatch` has NO `id` field. Applications link to a match by
the composite `(match_source, match_url)`. BOTH are required and
non-null at `create()`; empty strings are also rejected. Violations
raise `ValueError`.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from app.core import events
from app.modules.common.temporal_types import JobApplicationStatus
from app.modules.jobs import persistence
from app.modules.jobs._applications_status import (
    nightly_status as nightly_status,
)
from app.modules.jobs.job_status_transitions import check_transition
from app.modules.jobs.types import JobApplication


def _require(application_id: int, db_path: str | Path) -> JobApplication:
    existing = persistence.select_by_id(application_id, db_path=db_path)
    if existing is None:
        raise ValueError(f"job_application {application_id} not found")
    return existing


def _validate_match_composite(match_source: str, match_url: str) -> None:
    """Both match_source and match_url must be non-empty strings."""
    if match_source is None or not str(match_source).strip():
        raise ValueError(
            "match_source is required (non-null, non-empty) — matching.JobMatch "
            "has no id field so link via composite (match_source, match_url)"
        )
    if match_url is None or not str(match_url).strip():
        raise ValueError(
            "match_url is required (non-null, non-empty) — matching.JobMatch "
            "has no id field so link via composite (match_source, match_url)"
        )


def create(
    session_id: str,
    *,
    match_source: str,
    match_url: str,
    company: str,
    role: str,
    resume_version_id: int | None = None,
    db_path: str | Path,
) -> JobApplication:
    """Create a new job application.

    Composite match linkage: `(match_source, match_url)` stands in for the
    missing `matching.JobMatch.id`. Both required and non-null; empty
    strings are rejected. Initial status = DRAFT. Emits
    `job_application.created` with the stored row's JSON.
    """
    _validate_match_composite(match_source, match_url)
    application = JobApplication(
        session_id=session_id,
        match_source=match_source,
        match_url=match_url,
        company=company,
        role=role,
        resume_version_id=resume_version_id,
        status=JobApplicationStatus.DRAFT,
    )
    stored = persistence.insert(application, db_path=db_path)
    events.emit("job_application.created", stored.model_dump(mode="json"))
    return stored


def get(
    application_id: int, *, db_path: str | Path,
) -> JobApplication | None:
    return persistence.select_by_id(application_id, db_path=db_path)


def list_by_session(
    session_id: str, *, db_path: str | Path,
) -> list[JobApplication]:
    return persistence.select_by_session(session_id, db_path=db_path)


def list_by_status(
    session_id: str,
    status: JobApplicationStatus,
    *,
    db_path: str | Path,
) -> list[JobApplication]:
    return persistence.select_by_status(session_id, status, db_path=db_path)


def _build_status_changes(
    new_status: JobApplicationStatus,
    outcome_date: date | None,
) -> dict:
    """Assemble the UPDATE payload for a status transition.

    ``applied_date`` is set ONLY on the DRAFT→APPLIED transition. Other
    transitions ignore ``outcome_date`` to keep the field's semantics
    honest — a WITHDRAWN application must not look APPLIED.
    """
    changes: dict = {"status": new_status.value}
    if new_status is JobApplicationStatus.APPLIED:
        changes["applied_date"] = (
            outcome_date.isoformat() if outcome_date else date.today().isoformat()
        )
    return changes


def update_status(
    application_id: int,
    new_status: JobApplicationStatus,
    *,
    outcome_date: date | None = None,
    db_path: str | Path,
) -> JobApplication:
    """Transition a job application's status; emit `job_application.<status>`.

    Validates the transition via the ALLOWED matrix. Raises
    `InvalidJobStatusTransition` on disallowed moves.
    """
    current = _require(application_id, db_path)
    check_transition(current.status, new_status)
    changes = _build_status_changes(new_status, outcome_date)
    persistence.update_fields(application_id, changes, db_path=db_path)
    updated = _require(application_id, db_path)
    events.emit(
        f"job_application.{new_status.value}",
        updated.model_dump(mode="json"),
    )
    return updated


__all__ = [
    "create",
    "get",
    "list_by_session",
    "list_by_status",
    "nightly_status",
    "update_status",
]
