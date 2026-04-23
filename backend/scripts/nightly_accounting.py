"""Accounting helpers for the nightly orchestrator (T12.25).

Ported from ``ops:lib/nightly_accounting.py`` and adapted for the
MontGoWork backend: instead of per-date JSON files on disk, per-run
rows land in the ``nightly_run_log`` sqlite table (schema m002).

The on-disk session-log helpers (``save_session`` / ``load_session``)
are preserved as thin wrappers so the ops-side contract can be
reused by future diagnostics; they're not exercised by the nightly
cron path in S12a.
"""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

# Retained from the ops port; diagnostics consumers write here.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SESSIONS_DIR = _REPO_ROOT / "data" / "nightly-sessions"


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


def build_accounting_record(
    date_str: str,
    review: dict,
    plan_summary: dict,
    zoho_results: dict,
    *,
    systems: dict | None = None,
    voice: dict | None = None,
) -> dict:
    """Build a structured accounting record for a nightly session.

    Preserved from the ops port for backward compatibility with
    diagnostics tooling that may inspect on-disk session logs.
    """
    return {
        "date": date_str,
        "session_ts": datetime.utcnow().isoformat(),
        "review": {
            "dev": review.get("dev", {}),
            "engagement": review.get("engagement", {}),
            "time": review.get("time", {}),
            "leads": review.get("leads", {}),
        },
        "plan": {
            "blocks_count": plan_summary.get("blocks_count", 0),
            "carry_forward_count": plan_summary.get("carry_forward_count", 0),
            "categories": plan_summary.get("categories", []),
        },
        "zoho": {
            "created": zoho_results.get("created", 0),
            "skipped": zoho_results.get("skipped", 0),
            "errors": zoho_results.get("errors", []),
        },
        "systems": systems or {},
        "voice": voice or {},
        "meta": {"duration_seconds": 0},
    }


def save_session(date_str: str, record: dict) -> Path:
    """Atomically save a session record to data/nightly-sessions/{date}.json."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    target = SESSIONS_DIR / f"{date_str}.json"
    fd, tmp_path = tempfile.mkstemp(dir=SESSIONS_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(record, f, indent=2)
        os.replace(tmp_path, target)
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    return target


def load_session(date_str: str) -> dict | None:
    """Load a session record. Returns None if file doesn't exist."""
    target = SESSIONS_DIR / f"{date_str}.json"
    if not target.exists():
        return None
    return json.loads(target.read_text())


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
    "SESSIONS_DIR",
    "accounting_as_dict",
    "build_accounting_record",
    "insert_run_row",
    "load_session",
    "save_session",
    "url_to_path",
]
