"""SQLite persistence helpers for the job_applications table (T12.11).

Kept out of `applications.py` so the public lifecycle module stays under
the project's per-file function-count and line limits. Every function
opens a short-lived sqlite3 connection, operates, and closes — mirroring
`app.modules.appointments.persistence`.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from app.modules.common.temporal_types import JobApplicationStatus
from app.modules.jobs.types import JobApplication

_COLUMNS = (
    "id, session_id, match_source, match_url, company, role, "
    "resume_version_id, status, applied_date, created_at"
)

_INSERT_SQL = (
    "INSERT INTO job_applications "
    "(session_id, match_source, match_url, company, role, "
    "resume_version_id, status, applied_date, created_at) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
)

_SELECT_BY_ID_SQL = f"SELECT {_COLUMNS} FROM job_applications WHERE id = ?"
_SELECT_BY_SESSION_SQL = (
    f"SELECT {_COLUMNS} FROM job_applications WHERE session_id = ? "
    "ORDER BY created_at ASC, id ASC"
)
_SELECT_BY_STATUS_SQL = (
    f"SELECT {_COLUMNS} FROM job_applications "
    "WHERE session_id = ? AND status = ? "
    "ORDER BY created_at ASC, id ASC"
)


def _connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _parse_iso(raw: str | None) -> datetime | None:
    if not raw:
        return None
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    return date.fromisoformat(raw)


def _row_to_application(row: tuple) -> JobApplication:
    """Hydrate a DB row back into a JobApplication model."""
    (
        rid, session_id, match_source, match_url, company, role,
        resume_version_id, status, applied_date, created_at,
    ) = row
    return JobApplication(
        id=rid,
        session_id=session_id,
        match_source=match_source,
        match_url=match_url,
        company=company,
        role=role,
        resume_version_id=resume_version_id,
        status=JobApplicationStatus(status),
        applied_date=_parse_date(applied_date),
        created_at=_parse_iso(created_at),
    )


def insert(application: JobApplication, *, db_path: str | Path) -> JobApplication:
    """INSERT the application; return a copy with id + created_at populated."""
    created_at = application.created_at or datetime.now(timezone.utc)
    applied_iso = (
        application.applied_date.isoformat() if application.applied_date else None
    )
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            _INSERT_SQL,
            (
                application.session_id,
                application.match_source,
                application.match_url,
                application.company,
                application.role,
                application.resume_version_id,
                application.status.value,
                applied_iso,
                created_at.isoformat(),
            ),
        )
        conn.commit()
        new_id = int(cur.lastrowid)
    finally:
        conn.close()
    return application.model_copy(
        update={"id": new_id, "created_at": created_at},
    )


def select_by_id(
    application_id: int, *, db_path: str | Path,
) -> JobApplication | None:
    conn = _connect(db_path)
    try:
        row = conn.execute(_SELECT_BY_ID_SQL, (application_id,)).fetchone()
    finally:
        conn.close()
    return _row_to_application(row) if row else None


def select_by_session(
    session_id: str, *, db_path: str | Path,
) -> list[JobApplication]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(_SELECT_BY_SESSION_SQL, (session_id,)).fetchall()
    finally:
        conn.close()
    return [_row_to_application(r) for r in rows]


def select_by_status(
    session_id: str,
    status: JobApplicationStatus,
    *,
    db_path: str | Path,
) -> list[JobApplication]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            _SELECT_BY_STATUS_SQL, (session_id, status.value),
        ).fetchall()
    finally:
        conn.close()
    return [_row_to_application(r) for r in rows]


def update_fields(
    application_id: int,
    changes: dict,
    *,
    db_path: str | Path,
) -> None:
    """UPDATE only the provided columns. Caller supplies pre-serialized values."""
    if not changes:
        return
    sets = ", ".join(f"{col} = ?" for col in changes)
    params = list(changes.values()) + [application_id]
    conn = _connect(db_path)
    try:
        conn.execute(
            f"UPDATE job_applications SET {sets} WHERE id = ?", params,
        )
        conn.commit()
    finally:
        conn.close()


__all__ = [
    "insert",
    "select_by_id",
    "select_by_session",
    "select_by_status",
    "update_fields",
]
