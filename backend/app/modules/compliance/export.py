"""Worker data export — archive builder (T12.36).

Builds a ZIP containing ``data.json`` (every row the worker's session
is referenced from across the 13 S12 tables + ``sessions`` and
``record_profiles``) and ``summary.md`` (human-readable table of
contents).

Signed single-use download tokens live in :mod:`_export_tokens` to keep
this module under the functions-per-file ceiling. Public names are
re-exported so callers import from one place.
"""

from __future__ import annotations

import io
import json
import sqlite3
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from app.modules.compliance._export_tokens import (
    EXPORT_TTL_SEC,
    ComplianceTokenError,
    sign_export_token,
    verify_export_token,
)

__all__ = [
    "ComplianceTokenError",
    "EXPORT_TTL_SEC",
    "build_archive",
    "sign_export_token",
    "verify_export_token",
]


# Tables joined on session_id plus the special cases that join differently.
# Listed in stable order for deterministic archive output.
_SESSION_FK_TABLES: tuple[str, ...] = (
    "appointments",
    "job_applications",
    "resume_versions",
    "daily_progress_snapshots",
    "engagement_events",
    "plan_history",
    "outcomes_records",
    "reminder_cooldowns",
    "worker_unavailability",
    "record_profiles",
)


def build_archive(session_id: str, *, db_path: str | Path) -> bytes:
    """Return a ZIP (bytes) containing data.json + summary.md for a session."""
    session_row = _load_session_row(session_id, db_path)
    tables = _load_all_tables(session_id, db_path)
    generated_at = datetime.now(timezone.utc).isoformat()
    data = {
        "session_id": session_id,
        "generated_at": generated_at,
        "session": session_row,
        "tables": tables,
    }
    summary = _render_summary(session_id, tables, generated_at)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "data.json",
            json.dumps(data, indent=2, sort_keys=True, default=str),
        )
        zf.writestr("summary.md", summary)
    return buf.getvalue()


def _load_session_row(session_id: str, db_path: str | Path) -> dict | None:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def _load_all_tables(
    session_id: str, db_path: str | Path,
) -> dict[str, list[dict]]:
    """Return ``{table: [row_dict, ...]}`` for every session-FK table."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    out: dict[str, list[dict]] = {}
    try:
        for table in _SESSION_FK_TABLES:
            rows = conn.execute(
                f"SELECT * FROM {table} WHERE session_id = ?",
                (session_id,),
            ).fetchall()
            out[table] = [dict(r) for r in rows]
    finally:
        conn.close()
    return out


def _render_summary(
    session_id: str, tables: dict[str, list[dict]], generated_at: str,
) -> str:
    """Produce a human-readable markdown summary of the archive contents."""
    lines = [
        "# Worker Data Export",
        "",
        f"**Session**: `{session_id}`",
        f"**Generated**: {generated_at}",
        "",
        "## Tables",
        "",
    ]
    for table in _SESSION_FK_TABLES:
        lines.append(f"- `{table}`: {len(tables.get(table, []))} rows")
    lines.append("")
    lines.append(
        "See `data.json` for row-level detail. This archive is a "
        "point-in-time snapshot; regenerate for a fresh copy."
    )
    return "\n".join(lines) + "\n"
