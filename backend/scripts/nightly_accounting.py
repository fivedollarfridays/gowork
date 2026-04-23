"""Accounting helpers for the nightly orchestrator (T12.25).

Per-run rows land in the ``nightly_run_log`` sqlite table (schema m002).
The ops-style on-disk JSON session logs were removed — they had no
in-tree callers and the date-string in path concatenation carried
path-traversal risk. Restore from ops if future diagnostics need them,
but validate the date string first.
"""

from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class RunAccounting:
    """Summary of a single city's nightly run — mirrors nightly_run_log."""

    city: str
    sessions_processed: int
    emails_sent: int
    errors: int
    duration_sec: float
    start_ts: datetime
    end_ts: datetime


def url_to_path(url: str) -> Path:
    """Extract the filesystem path from a ``sqlite+aiosqlite:///...`` URL."""
    marker = ":///"
    idx = url.find(marker)
    return Path(url[idx + len(marker):] if idx != -1 else url)


def insert_run_row(db_path: str | Path, acct: RunAccounting) -> None:
    """Insert a single ``nightly_run_log`` row from a ``RunAccounting``."""
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO nightly_run_log "
            "(city, sessions_processed, emails_sent, errors, "
            "duration_sec, start_ts, end_ts) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                acct.city,
                acct.sessions_processed,
                acct.emails_sent,
                acct.errors,
                acct.duration_sec,
                acct.start_ts.isoformat(),
                acct.end_ts.isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def accounting_as_dict(acct: RunAccounting) -> dict:
    """Return a JSON-serializable dict for a RunAccounting row."""
    out = asdict(acct)
    out["start_ts"] = acct.start_ts.isoformat()
    out["end_ts"] = acct.end_ts.isoformat()
    return out


__all__ = [
    "RunAccounting",
    "accounting_as_dict",
    "insert_run_row",
    "url_to_path",
]
