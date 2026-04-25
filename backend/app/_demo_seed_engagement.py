"""Engagement + reminder + advisor spokes for the QC demo seed (T13.2).

Plants:

* ``engagement_events`` rows shaping a 7-day window per session
  (varied volume by stall state).
* ``sendgrid_events`` 'open' rows for sessions whose state plan
  requests them (used by the weekly-review composer to compute
  open rates).
* ``reminder_cooldowns`` + ``reminders_auto_disabled`` rows so
  cooldown + opt-out QC paths exercise real state.
* One ``advisor_tokens`` row per city.

Every helper is idempotent on a populated DB.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta


__all__ = [
    "seed_engagement_window",
    "seed_reminder_state",
    "seed_advisor_token",
    "advisor_token_plaintext",
]


def _slot_token(session_id: str, slot: str) -> str:
    digest = hashlib.sha256(f"qc:{session_id}:{slot}".encode()).hexdigest()
    return f"demo-{slot}-{digest[:24]}"


def _iso(dt: datetime) -> str:
    return dt.isoformat()


# -------------------- Weekly review (engagement window) --------------------


def _engagement_plan(state_label: str) -> dict:
    """Volume + shape of engagement signals per stall state."""
    if state_label in ("none", "soft"):
        return {
            "events": [
                ("digest_sent", 1), ("digest_sent", 3), ("digest_sent", 5),
                ("reminder_sent", 4),
            ],
            "seed_open": True,
        }
    if state_label == "medium":
        return {
            "events": [
                ("digest_sent", 2),
                ("stall_soft", 4), ("stall_medium", 5),
            ],
            "seed_open": False,
        }
    return {
        "events": [("digest_sent", 6), ("stall_hard", 5)],
        "seed_open": False,
    }


def seed_engagement_window(
    conn: sqlite3.Connection,
    session_id: str,
    state_label: str,
    now: datetime,
) -> None:
    """Plant 7-day engagement signals; idempotent on (session, category, ts)."""
    plan = _engagement_plan(state_label)
    payload = json.dumps({"demo": True, "slot": "weekly_review"})
    for category, days_ago in plan["events"]:
        ts = _iso(now - timedelta(days=days_ago))
        existing = conn.execute(
            "SELECT 1 FROM engagement_events "
            "WHERE session_id = ? AND category = ? AND created_at = ? "
            "LIMIT 1",
            (session_id, category, ts),
        ).fetchone()
        if existing is not None:
            continue
        conn.execute(
            "INSERT INTO engagement_events "
            "(session_id, category, payload_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, category, payload, ts),
        )
    if plan["seed_open"]:
        _seed_sendgrid_open(conn, session_id, now)


def _seed_sendgrid_open(
    conn: sqlite3.Connection, session_id: str, now: datetime,
) -> None:
    """Plant one 'open' event keyed by deterministic message_id."""
    email = _resolve_or_set_session_email(conn, session_id)
    if email is None:
        return
    msg_id = _slot_token(session_id, "sendgrid-msg")
    existing = conn.execute(
        "SELECT 1 FROM sendgrid_events WHERE message_id = ? LIMIT 1",
        (msg_id,),
    ).fetchone()
    if existing is not None:
        return
    ts = _iso(now - timedelta(days=2, hours=3))
    conn.execute(
        "INSERT INTO sendgrid_events "
        "(event_type, email, message_id, reason, raw_payload_json, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            "open", email, msg_id, None,
            json.dumps({"demo": True}), ts,
        ),
    )


def _resolve_or_set_session_email(
    conn: sqlite3.Connection, session_id: str,
) -> str | None:
    """Return profile.email; set a deterministic demo email when absent."""
    row = conn.execute(
        "SELECT profile FROM sessions WHERE id = ?", (session_id,),
    ).fetchone()
    if row is None:
        return None
    try:
        profile = json.loads(row[0]) if row[0] else {}
    except (json.JSONDecodeError, TypeError):
        profile = {}
    if not isinstance(profile, dict):
        profile = {}
    if profile.get("email"):
        return str(profile["email"])
    profile["email"] = f"demo-{session_id[:8]}@example.invalid"
    profile["first_name"] = profile.get("first_name") or "Demo"
    conn.execute(
        "UPDATE sessions SET profile = ? WHERE id = ?",
        (json.dumps(profile), session_id),
    )
    return profile["email"]


# -------------------- Reminder state --------------------


def seed_reminder_state(
    conn: sqlite3.Connection,
    session_id: str,
    state_label: str,
    now: datetime,
) -> None:
    """Plant reminder cooldown + opt-out rows keyed by stall state.

    - ``soft`` → SOFT cooldown (worker engaged; cooldown gate).
    - ``hard`` → HARD cooldown + ``reminders_auto_disabled`` (opted out).
    - others → no cooldown row (engagement_events already plants reminders).
    """
    if state_label == "soft":
        _insert_cooldown(conn, session_id, "stall_soft", level=1, now=now)
    elif state_label == "hard":
        _insert_cooldown(conn, session_id, "stall_hard", level=3, now=now)
        _insert_engagement_event(
            conn, session_id, "reminders_auto_disabled", now,
            payload={"demo": True, "reason": "worker_opt_out"},
        )


def _insert_cooldown(
    conn: sqlite3.Connection, session_id: str, category: str,
    *, level: int, now: datetime,
) -> None:
    existing = conn.execute(
        "SELECT 1 FROM reminder_cooldowns "
        "WHERE session_id = ? AND category = ? LIMIT 1",
        (session_id, category),
    ).fetchone()
    if existing is not None:
        return
    conn.execute(
        "INSERT INTO reminder_cooldowns "
        "(session_id, category, last_sent_at, stall_level) "
        "VALUES (?, ?, ?, ?)",
        (session_id, category, _iso(now - timedelta(hours=12)), level),
    )


def _insert_engagement_event(
    conn: sqlite3.Connection,
    session_id: str,
    category: str,
    now: datetime,
    *,
    payload: dict | None = None,
) -> None:
    existing = conn.execute(
        "SELECT 1 FROM engagement_events "
        "WHERE session_id = ? AND category = ? "
        "AND json_extract(payload_json, '$.demo') = 1 LIMIT 1",
        (session_id, category),
    ).fetchone()
    if existing is not None:
        return
    conn.execute(
        "INSERT INTO engagement_events "
        "(session_id, category, payload_json, created_at) "
        "VALUES (?, ?, ?, ?)",
        (
            session_id, category,
            json.dumps(payload or {"demo": True}, sort_keys=True),
            _iso(now),
        ),
    )


# -------------------- Advisor token --------------------


def advisor_token_plaintext(city: str) -> str:
    """Build the deterministic mw_adv_-style token plaintext for a city."""
    digest = hashlib.sha256(f"qc-advisor:{city}".encode()).hexdigest()
    return f"mw_adv_demo_{city}_{digest[:24]}"


def seed_advisor_token(
    conn: sqlite3.Connection, city: str, now: datetime,
) -> None:
    """Plant one ``advisor_tokens`` row per city (active, never revoked)."""
    plaintext = advisor_token_plaintext(city)
    token_hash = hashlib.sha256(plaintext.encode("utf-8")).hexdigest()
    advisor_id = f"adv-demo-{city}"
    existing = conn.execute(
        "SELECT 1 FROM advisor_tokens WHERE token_hash = ? LIMIT 1",
        (token_hash,),
    ).fetchone()
    if existing is not None:
        return
    conn.execute(
        "INSERT INTO advisor_tokens "
        "(token_hash, advisor_id, city, issued_at, revoked_at, expires_at) "
        "VALUES (?, ?, ?, ?, NULL, NULL)",
        (token_hash, advisor_id, city, _iso(now)),
    )
