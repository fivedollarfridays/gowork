"""Engagement digest preview route (T12.21a, S12a).

Single endpoint — the minimal slice of T12.21 required for frontend
T12.29. Renders today's worker digest via T12.20 ``compose_digest``
without sending email. The remaining four engagement endpoints (events,
preferences, send-now, unsubscribe) land in S12b T12.21.

Auth + session ownership semantics mirror :mod:`app.routes.appointments`:
``token`` is validated against the ``feedback_tokens`` table and must
match the ``session_id`` query parameter (403 on cross-session access).
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.core.config import get_settings
from app.core.day_boundary import current_work_date
from app.modules.engagement.digest_composer import compose_digest
from app.routes import _appointments_helpers as _h

router = APIRouter(prefix="/api/engagement", tags=["engagement"])


def _resolve_db_path() -> str:
    """Indirection so tests can monkeypatch the DB path in one place."""
    return _h.resolve_db_path()


def _parse_for_date(raw: str | None) -> date:
    """Return the digest's target date.

    Defaults to today's city-local work date (per app.core.day_boundary)
    when ``raw`` is None. Raises 400 on a malformed ISO string rather
    than Pydantic's default 422 so the contract is transparent.
    """
    if raw is None:
        return current_work_date(get_settings().city)
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"for_date must be ISO yyyy-mm-dd (got {raw!r})",
        ) from exc


@router.get("/preview-digest")
def preview_digest(
    session_id: str = Query(...),
    token: str = Query(...),
    for_date: str | None = Query(None),
) -> dict:
    """Preview a worker's digest for ``for_date`` (default today, city-local).

    Renders via T12.20 ``compose_digest``; does NOT send email. Returns
    ``{subject, html, text, section_counts}``.
    """
    db_path = _resolve_db_path()
    _h.verify_token(db_path, session_id, token)
    target_date = _parse_for_date(for_date)
    result = compose_digest(session_id, target_date, db_path=db_path)
    return {
        "subject": result.subject,
        "html": result.html,
        "text": result.text,
        "section_counts": result.section_counts,
    }


__all__ = ["router"]
