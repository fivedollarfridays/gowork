"""Job-applications API router (T12.13).

Five endpoints under ``/api/job-applications`` — intentionally hyphenated
to avoid collision with the existing ``/api/jobs/{job_id}`` resource
owned by :mod:`app.routes.jobs` (aggregated job listings):

- GET    /api/job-applications?session_id=X
- POST   /api/job-applications
- PATCH  /api/job-applications/{id}          (status-only)
- GET    /api/job-applications/funnel?session_id=X
- GET    /api/job-applications/community-funnel?segment_by=X

Auth contract mirrors T12.10 appointments: every endpoint requires a
``token`` query param backed by ``feedback_tokens``. Session-owned
endpoints enforce that the token's ``session_id`` matches the target
row (403 otherwise).

Community-funnel city determination comes from the authenticated
session's own ``outcomes_records`` tag (never a query param) so a
session cannot probe another city's aggregate. Falls back to
``settings.city`` when the session carries no tag.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from app.modules.common.temporal_types import JobApplicationStatus
from app.modules.documents import _versions_db as _resume_versions  # T12.17 hook
from app.modules.jobs import applications, funnel_analytics
from app.modules.jobs.job_status_transitions import InvalidJobStatusTransition
from app.modules.jobs.types import JobApplication
from app.routes import _appointments_helpers as _h

router = APIRouter(prefix="/api/job-applications", tags=["job-applications"])


def _resolve_db_path() -> str:
    """Indirection so tests can monkeypatch the DB path in one place."""
    return _h.resolve_db_path()


# -------------------- Request bodies --------------------


class ApplicationCreate(BaseModel):
    """POST body — the subset of JobApplication fields callers supply."""

    session_id: str
    match_source: str
    match_url: str
    company: str | None = None
    role: str | None = None
    resume_version_id: int | None = None


class ApplicationStatusPatch(BaseModel):
    """PATCH body — status-only; extra fields rejected at 400 (not 422).

    ``extra="allow"`` so the handler can emit a precise business-rule
    error for non-status mutations rather than a schema-level 422.
    """

    model_config = ConfigDict(extra="allow")

    status: JobApplicationStatus | None = None
    outcome_date: str | None = None  # ISO date string, optional


# -------------------- Helpers --------------------


def _resolve_session_city(db_path: str, session_id: str) -> str:
    """Return the city tag for a session; fall back to ``settings.city``.

    Looks up the most recent ``outcomes_records.payload_json.city`` for
    the session. Anchored in the authenticated session, never the caller
    — this prevents cross-city probing on ``/community-funnel``.
    """
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT json_extract(payload_json, '$.city') FROM outcomes_records "
            "WHERE session_id = ? "
            "AND json_extract(payload_json, '$.city') IS NOT NULL "
            "ORDER BY created_at DESC LIMIT 1",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()
    if row and row[0]:
        return str(row[0])
    from app.core.config import get_settings
    return get_settings().city


def _load_owned_application(
    application_id: int, session_id: str, *, db_path: str,
) -> JobApplication:
    """Fetch an application; 404 if missing, 403 if cross-session."""
    app = applications.get(application_id, db_path=db_path)
    if app is None:
        raise HTTPException(
            status_code=404, detail="Job application not found",
        )
    if app.session_id != session_id:
        raise HTTPException(
            status_code=403,
            detail="Application belongs to another session",
        )
    return app


def _patch_to_status_change(patch: ApplicationStatusPatch) -> tuple[
    JobApplicationStatus, Any,
]:
    """Extract (status, outcome_date) from PATCH body; 400 on illegal fields."""
    raw = patch.model_dump(exclude_unset=True)
    allowed = {"status", "outcome_date"}
    extras = [k for k in raw if k not in allowed]
    if extras:
        raise HTTPException(
            status_code=400,
            detail=(
                f"field(s) {extras!r} cannot be changed via PATCH — "
                "only 'status' (and optional 'outcome_date') are accepted"
            ),
        )
    if patch.status is None:
        raise HTTPException(
            status_code=400, detail="'status' is required for PATCH",
        )
    outcome_date = None
    if patch.outcome_date:
        from datetime import date as _date
        try:
            outcome_date = _date.fromisoformat(patch.outcome_date)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"outcome_date must be ISO-8601 date: {exc}",
            ) from exc
    return patch.status, outcome_date


# -------------------- GET / POST --------------------


@router.get("", response_model=list[JobApplication])
def list_applications(
    session_id: str = Query(...), token: str = Query(...),
) -> list[JobApplication]:
    """Return every application attached to the authenticated session."""
    db_path = _resolve_db_path()
    _h.verify_token(db_path, session_id, token)
    return applications.list_by_session(session_id, db_path=db_path)


@router.post("", response_model=JobApplication, status_code=201)
def create_application(
    body: ApplicationCreate, token: str = Query(...),
) -> JobApplication:
    """Create a new application. 403 if body.session_id ≠ token session."""
    db_path = _resolve_db_path()
    _h.verify_token(db_path, body.session_id, token)
    try:
        created = applications.create(
            body.session_id,
            match_source=body.match_source,
            match_url=body.match_url,
            company=body.company or "",
            role=body.role or "",
            resume_version_id=body.resume_version_id,
            db_path=db_path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    # T12.17 hook: when an application links to a specific resume
    # version, bump that version's ``use_counter``. Best-effort —
    # ``increment_use_counter`` no-ops on a stale id rather than 500.
    if body.resume_version_id is not None:
        _resume_versions.increment_use_counter(
            body.resume_version_id, db_path=db_path,
        )
    return created


# -------------------- PATCH /{id} --------------------


@router.patch("/{application_id}", response_model=JobApplication)
def patch_application(
    application_id: int,
    patch: ApplicationStatusPatch,
    token: str = Query(...),
) -> JobApplication:
    """Transition an application's status. 409 on disallowed transition."""
    db_path = _resolve_db_path()
    session_id = _h.resolve_session_from_token(db_path, token)
    _load_owned_application(application_id, session_id, db_path=db_path)
    new_status, outcome_date = _patch_to_status_change(patch)
    try:
        return applications.update_status(
            application_id, new_status,
            outcome_date=outcome_date, db_path=db_path,
        )
    except InvalidJobStatusTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


# -------------------- Funnel endpoints --------------------


@router.get("/funnel")
def get_session_funnel(
    session_id: str = Query(...), token: str = Query(...),
) -> dict:
    """Per-session funnel counts and conversion rates."""
    db_path = _resolve_db_path()
    _h.verify_token(db_path, session_id, token)
    result = funnel_analytics.compute_funnel(session_id, db_path=db_path)
    return json.loads(result.model_dump_json())


@router.get("/community-funnel")
def get_community_funnel(
    token: str = Query(...),
    segment_by: str | None = Query(None),
) -> dict:
    """Community-wide funnel scoped to the authenticated session's city.

    k-anonymity suppression (min 5 distinct sessions per cell) is applied
    inside :mod:`funnel_analytics`. The city is resolved from the
    session's own outcomes_records tag — never from a query parameter —
    to prevent cross-city probing.
    """
    db_path = _resolve_db_path()
    session_id = _h.resolve_session_from_token(db_path, token)
    city = _resolve_session_city(db_path, session_id)
    raw = funnel_analytics.compute_community_funnel(
        city, segment_by=segment_by, db_path=db_path,  # type: ignore[arg-type]
    )
    return {k: json.loads(v.model_dump_json()) for k, v in raw.items()}
