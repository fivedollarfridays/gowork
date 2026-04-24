"""Shared ``nightly_status`` helper for the two document builders (T12.25b).

``resume_builder`` and ``cover_letter_builder`` both persist to the same
``resume_versions`` table and classify health the same way: healthy when
the newest row is ≤ 7 days old, degraded when versions exist but are
stale, unknown when none exist. Extracting the logic here keeps both
builder modules under the 15-function / 400-line arch budget.

This helper is private to the documents package — it's only imported
from inside :func:`resume_builder.nightly_status` and
:func:`cover_letter_builder.nightly_status`.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.modules.common.temporal_types import ModuleStatus

_STALE_DAYS = 7


def build_status(
    session_id: str,
    *,
    module_name: str,
    doc_type: str,
    count_key: str,
    db_path: str | Path,
    now: datetime | None = None,
) -> ModuleStatus:
    """Compose a :class:`ModuleStatus` from ``resume_versions`` activity."""
    reference = now or datetime.now(timezone.utc)
    count, last_at = _read_activity(
        session_id, doc_type=doc_type, db_path=db_path,
    )
    health, note = _classify(count=count, last_at=last_at, now=reference)
    signals: dict[str, Any] = {count_key: count, "note": note}
    return ModuleStatus(
        module_name=module_name,
        health=health, signals=signals, last_activity_at=last_at,
    )


def _read_activity(
    session_id: str, *, doc_type: str, db_path: str | Path,
) -> tuple[int, datetime | None]:
    """Return ``(count, last_created_at)`` for one session + doc_type."""
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT COUNT(*), MAX(created_at) FROM resume_versions "
            "WHERE session_id = ? AND doc_type = ?",
            (session_id, doc_type),
        ).fetchone()
    finally:
        conn.close()
    count = int(row[0]) if row and row[0] is not None else 0
    last_raw = row[1] if row else None
    last_at = _parse_iso(last_raw) if last_raw else None
    return count, last_at


def _parse_iso(value: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _classify(
    *, count: int, last_at: datetime | None, now: datetime,
) -> tuple[str, str]:
    """Shared healthy / degraded / unknown rule for document modules."""
    if count == 0 or last_at is None:
        return "unknown", "no versions"
    age_days = (now - last_at).days
    if age_days <= _STALE_DAYS:
        return "healthy", "recent activity"
    return "degraded", f"stale — last version {age_days}d ago"


def resume_nightly_status(
    session_id: str, *, db_path: str | Path, now: datetime | None = None,
) -> ModuleStatus:
    """Concrete ``nightly_status`` entry point for :mod:`resume_builder`."""
    return build_status(
        session_id,
        module_name="resume_builder",
        doc_type="resume", count_key="resume_count",
        db_path=db_path, now=now,
    )


def cover_letter_nightly_status(
    session_id: str, *, db_path: str | Path, now: datetime | None = None,
) -> ModuleStatus:
    """Concrete ``nightly_status`` entry point for :mod:`cover_letter_builder`."""
    return build_status(
        session_id,
        module_name="cover_letter_builder",
        doc_type="cover_letter", count_key="cover_letter_count",
        db_path=db_path, now=now,
    )


__all__ = [
    "build_status",
    "cover_letter_nightly_status",
    "resume_nightly_status",
]
