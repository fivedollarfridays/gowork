"""Reminder / digest cooldown state (T12.19, S12b).

Backed by the ``reminder_cooldowns`` table (m002). Dedup key is
``(session_id, category)`` — NOT ``(session_id, barrier_id)`` — so a
multi-barrier stalled session produces exactly ONE email per stall
level per 24h window.

Categories in use:
    stall_soft, stall_medium, stall_hard, digest

A SOFT→MEDIUM→HARD transition writes three independent rows (different
categories) so the worker sees one email at each escalation.

Ported from ``ops:lib/cooldown.py`` — same contract, SQLite-backed.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

__all__ = [
    "DEDUP_WINDOW",
    "check_cooldown",
    "record_send",
    "get_cooldown_status",
]

DEDUP_WINDOW = timedelta(hours=24)


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(timezone.utc)


def _latest_row(
    db_path: str | Path,
    session_id: str,
    category: str,
) -> tuple[str, int] | None:
    """Return (last_sent_at_iso, stall_level) for the most recent row or None."""
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT last_sent_at, stall_level FROM reminder_cooldowns "
            "WHERE session_id = ? AND category = ? "
            "ORDER BY datetime(last_sent_at) DESC LIMIT 1",
            (session_id, category),
        ).fetchone()
    finally:
        conn.close()
    return row


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def check_cooldown(
    session_id: str,
    category: str,
    *,
    db_path: str | Path,
    now: datetime | None = None,
) -> bool:
    """Return True if it's SAFE to send (no recent dupe within 24h)."""
    resolved_now = _now(now)
    row = _latest_row(db_path, session_id, category)
    if row is None:
        return True
    last_sent = _parse_iso(row[0])
    if last_sent is None:
        return True
    return (resolved_now - last_sent) >= DEDUP_WINDOW


_STALL_LEVEL_RANK = {None: 0, "none": 0, "soft": 1, "medium": 2, "hard": 3}


def _level_to_int(stall_level: str | None) -> int:
    if stall_level is None:
        return 0
    return _STALL_LEVEL_RANK.get(stall_level.lower(), 0)


def record_send(
    session_id: str,
    category: str,
    stall_level: str | None,
    *,
    db_path: str | Path,
    now: datetime | None = None,
) -> None:
    """Write a reminder_cooldowns row after a successful send."""
    resolved_now = _now(now)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO reminder_cooldowns "
            "(session_id, category, last_sent_at, stall_level) "
            "VALUES (?, ?, ?, ?)",
            (
                session_id,
                category,
                resolved_now.isoformat(),
                _level_to_int(stall_level),
            ),
        )
        conn.commit()
    finally:
        conn.close()


_INT_TO_LEVEL = {0: None, 1: "soft", 2: "medium", 3: "hard"}


def get_cooldown_status(
    session_id: str,
    *,
    db_path: str | Path,
) -> dict[str, dict[str, Any]]:
    """Return {category: {last_sent_at, stall_level}} for observability."""
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT category, last_sent_at, stall_level FROM reminder_cooldowns "
            "WHERE session_id = ? "
            "ORDER BY datetime(last_sent_at) DESC",
            (session_id,),
        ).fetchall()
    finally:
        conn.close()
    out: dict[str, dict[str, Any]] = {}
    for category, last_sent_at, stall_level_int in rows:
        if category in out:
            continue  # already captured the most recent
        out[category] = {
            "last_sent_at": last_sent_at,
            "stall_level": _INT_TO_LEVEL.get(stall_level_int),
        }
    return out


def _apply_cooldown_filter(
    candidates: list[dict[str, Any]],
    *,
    db_path: str | Path,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Drop items whose (session_id, category) is on cooldown.

    Each candidate dict must carry ``session_id`` and ``category`` keys.
    Unknown or missing keys cause the item to be kept (safe default).
    """
    resolved_now = _now(now)
    kept: list[dict[str, Any]] = []
    for item in candidates:
        sid = item.get("session_id")
        cat = item.get("category")
        if not sid or not cat:
            kept.append(item)
            continue
        if check_cooldown(sid, cat, db_path=db_path, now=resolved_now):
            kept.append(item)
    return kept
