"""Worker-facing compliance endpoints (T12.36).

Three endpoints, each gated on the worker's feedback_token (session-
ownership) and rate-limited at 3/hour per session:

* ``POST /api/compliance/export``
* ``POST /api/compliance/delete``
* ``POST /api/compliance/delete/selective``

Authority model
---------------
Authentication is the existing ``feedback_tokens`` row (same scheme the
appointments routes use). The caller passes ``(session_id, session_token)``
and we verify the token maps to that exact session via
``_appointments_helpers.verify_token``. Cross-session tokens return 403.

Rate limiting
-------------
Per-session, not per-IP. Same algorithm as the feature-flag toggle
endpoint but with a tighter (3/hour) quota — right-to-delete needs to
be reachable, but not spammable, and high-volume export requests are a
signal of compromise.

Export archive storage
----------------------
Archives live only in memory — the endpoint builds, signs a 24h-TTL
single-use token, and returns a URL pointing at ``GET /api/compliance/
export/download?token=...`` that rebuilds the archive on demand.
Out-of-scope for this ticket: persistent archive storage + a dedicated
CDN. The in-memory rebuild path is safe because the source rows haven't
been deleted yet (export precedes delete in the worker journey).
"""

from __future__ import annotations

import hashlib
import logging
import threading
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from app.modules.compliance import delete as delete_mod
from app.modules.compliance import export as export_mod
from app.routes import _appointments_helpers as _auth_helpers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/compliance", tags=["compliance"])

# Per-session quota. Lower than the admin flag limit (10/h) because a
# worker legitimately never needs >3 of these per hour.
_RATE_LIMIT_MAX = 3
_RATE_LIMIT_WINDOW = timedelta(hours=1)
_RATE_LIMITER: dict[str, list[datetime]] = {}
_RATE_LOCK = threading.Lock()


def _resolve_db_path() -> str:
    """Shared DB-path resolver — monkeypatched by tests."""
    return _auth_helpers.resolve_db_path()


def _enforce_rate_limit(session_id: str) -> None:
    """Raise 429 when the session has hit its per-hour quota."""
    now = datetime.now(timezone.utc)
    cutoff = now - _RATE_LIMIT_WINDOW
    with _RATE_LOCK:
        history = [
            ts for ts in _RATE_LIMITER.get(session_id, []) if ts > cutoff
        ]
        if len(history) >= _RATE_LIMIT_MAX:
            _RATE_LIMITER[session_id] = history
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded: 3 requests per hour per session",
            )
        history.append(now)
        _RATE_LIMITER[session_id] = history


# --------------------------------------------------------------- request bodies

class ExportRequest(BaseModel):
    """POST body for ``/api/compliance/export``."""

    session_id: str = Field(..., min_length=1)
    session_token: str = Field(..., min_length=1)


class DeleteRequest(BaseModel):
    """POST body for ``/api/compliance/delete`` (full delete)."""

    session_id: str = Field(..., min_length=1)
    session_token: str = Field(..., min_length=1)
    confirm: str = Field(..., description="Must equal 'DELETE' to proceed")
    reason: str = Field(default="worker_request", max_length=500)


class SelectiveDeleteRequest(BaseModel):
    """POST body for ``/api/compliance/delete/selective``."""

    session_id: str = Field(..., min_length=1)
    session_token: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=64)
    reason: str = Field(default="worker_request", max_length=500)


# --------------------------------------------------------------- endpoints

@router.post("/export")
def request_export(body: ExportRequest) -> dict:
    """Build an archive + return a signed single-use download URL (24h TTL)."""
    db_path = _resolve_db_path()
    _auth_helpers.verify_token(db_path, body.session_id, body.session_token)
    _enforce_rate_limit(body.session_id)
    archive_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    token = export_mod.sign_export_token(
        body.session_id, archive_id=archive_id,
    )
    from app.modules.compliance._audit import write_audit
    write_audit(
        db_path=db_path, session_id=body.session_id,
        action="export_requested", actor_token=body.session_token,
        payload={"archive_id": archive_id},
    )
    return {
        "archive_id": archive_id,
        "download_url": f"/api/compliance/export/download?token={token}",
        "expires_in_sec": export_mod.EXPORT_TTL_SEC,
    }


@router.get("/export/download")
def download_export(token: str = Query(...)) -> Response:
    """Consume the signed token, stream the ZIP archive (single-use)."""
    db_path = _resolve_db_path()
    try:
        session_id, _arc = export_mod.verify_export_token(
            token, db_path=db_path,
        )
    except export_mod.ComplianceTokenError:
        logger.debug("compliance download rejected", exc_info=True)
        raise HTTPException(
            status_code=401, detail="Invalid or expired download token",
        ) from None
    from app.modules.compliance._audit import write_audit
    # S7: audit BEFORE build so a failed archive still leaves a trail.
    # On build failure we also write an export_failed row so the
    # compliance trail survives a 500.
    write_audit(
        db_path=db_path, session_id=session_id,
        action="export_downloaded",
    )
    try:
        archive = export_mod.build_archive(session_id, db_path=db_path)
    except Exception as exc:
        write_audit(
            db_path=db_path, session_id=session_id,
            action="export_failed",
            payload={"error_class": type(exc).__name__},
        )
        raise
    # S6: filename uses a stable SHA256 prefix of the session_id, not the
    # raw worker-controlled value (which has no CR/LF/quote constraint
    # at schema level and could plant header bytes).
    safe_id = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:16]
    return Response(
        content=archive,
        media_type="application/zip",
        headers={
            "Content-Disposition": (
                f"attachment; filename=worker-data-{safe_id}.zip"
            ),
        },
    )


@router.post("/delete")
def request_full_delete(body: DeleteRequest) -> dict:
    """Cascade-delete every row tied to the session. Irreversible."""
    if body.confirm != "DELETE":
        raise HTTPException(
            status_code=400,
            detail="confirm must equal 'DELETE' to proceed",
        )
    db_path = _resolve_db_path()
    _auth_helpers.verify_token(db_path, body.session_id, body.session_token)
    _enforce_rate_limit(body.session_id)
    delete_mod.full_delete(
        body.session_id, db_path=db_path,
        reason=body.reason, actor_token=body.session_token,
    )
    return {"session_id": body.session_id, "status": "deleted"}


@router.post("/delete/selective")
def request_selective_delete(body: SelectiveDeleteRequest) -> dict:
    """Tombstone the rows tied to ``category`` (soft-delete, reversible)."""
    db_path = _resolve_db_path()
    _auth_helpers.verify_token(db_path, body.session_id, body.session_token)
    _enforce_rate_limit(body.session_id)
    try:
        delete_mod.selective_delete(
            body.session_id, category=body.category, db_path=db_path,
            reason=body.reason, actor_token=body.session_token,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    return {
        "session_id": body.session_id,
        "category": body.category,
        "status": "tombstoned",
    }


__all__ = ["router"]
