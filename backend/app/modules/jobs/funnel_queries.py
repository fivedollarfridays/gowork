"""DB access helpers for `funnel_analytics` (T12.12).

Kept in a sibling module so `funnel_analytics.py` stays under the
project's per-file function/line limits. Every function opens a
short-lived sqlite3 connection and closes it — mirroring
`app.modules.jobs.persistence`.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def has_demo_column(conn: sqlite3.Connection) -> bool:
    rows = conn.execute("PRAGMA table_info(sessions)").fetchall()
    return any(r[1] == "demo" for r in rows)


def city_scoped_session_ids(city: str, db_path: str | Path) -> set[str]:
    """Sessions with ≥1 outcomes_records row tagged with the given city.

    Applies the demo-session guard (column-aware). When
    `sessions.demo` exists, rows with `demo=1` are excluded.
    """
    conn = connect(db_path)
    try:
        demo_clause = ""
        if has_demo_column(conn):
            demo_clause = (
                " AND EXISTS (SELECT 1 FROM sessions s "
                "WHERE s.id = outcomes_records.session_id "
                "AND COALESCE(s.demo, 0) = 0)"
            )
        sql = (
            "SELECT DISTINCT session_id FROM outcomes_records "
            "WHERE json_extract(payload_json, '$.city') = ?" + demo_clause
        )
        rows = conn.execute(sql, (city,)).fetchall()
    finally:
        conn.close()
    return {r[0] for r in rows}


def fetch_status_rows_for_session(
    session_id: str, db_path: str | Path,
) -> list[tuple[int, str]]:
    conn = connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, status FROM job_applications WHERE session_id = ?",
            (session_id,),
        ).fetchall()
    finally:
        conn.close()
    return [(r[0], r[1]) for r in rows]


def fetch_status_rows_for_sessions(
    session_ids: set[str], db_path: str | Path,
) -> list[tuple[str, str]]:
    if not session_ids:
        return []
    placeholders = ",".join(["?"] * len(session_ids))
    conn = connect(db_path)
    try:
        rows = conn.execute(
            f"SELECT session_id, status FROM job_applications "
            f"WHERE session_id IN ({placeholders})",
            tuple(session_ids),
        ).fetchall()
    finally:
        conn.close()
    return [(r[0], r[1]) for r in rows]


def fetch_company_rows_for_sessions(
    session_ids: set[str], db_path: str | Path,
) -> list[tuple[str, str]]:
    if not session_ids:
        return []
    placeholders = ",".join(["?"] * len(session_ids))
    conn = connect(db_path)
    try:
        rows = conn.execute(
            f"SELECT session_id, company FROM job_applications "
            f"WHERE session_id IN ({placeholders})",
            tuple(session_ids),
        ).fetchall()
    finally:
        conn.close()
    return [(r[0], r[1] or "") for r in rows]


def load_cleared_barriers(
    session_id: str, db_path: str | Path,
) -> list[str]:
    """Read `profile.cleared_barriers` (list) from `sessions.profile` JSON."""
    conn = connect(db_path)
    try:
        row = conn.execute(
            "SELECT profile FROM sessions WHERE id = ?", (session_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row or not row[0]:
        return []
    try:
        profile = json.loads(row[0])
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(profile, dict):
        return []
    cleared = profile.get("cleared_barriers") or []
    return list(cleared) if isinstance(cleared, list) else []


__all__ = [
    "city_scoped_session_ids",
    "connect",
    "fetch_company_rows_for_sessions",
    "fetch_status_rows_for_session",
    "fetch_status_rows_for_sessions",
    "has_demo_column",
    "load_cleared_barriers",
]
