"""Tests for S13 T13.2 — QC demo-seed extension.

Cycles (continuing the numbering from ``test_demo_seed_s12b.py``):

- Cycle 7: Compliance state — feedback tokens (active + expired) and
           baseline compliance_audit rows.
- Cycle 8: Weekly review state — varied 7-day engagement windows per
           session.
- Cycle 9: Advisor inbox state — advisor_tokens per city, scoped
           correctly.
- Cycle 10: Reminder state — reminder_sent + reminders_auto_disabled
            rows with cooldown entries.
- Cycle 11: Module-status coverage — every module key has at least one
            demo session with non-unknown health.
- Cycle 12: Determinism + idempotency on the full QC payload.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.demo_seed import seed_worker_companion_sessions
from app.modules.advisor import repository as advisor_repo
from app.modules.engagement import reminder_engine
from app.modules.plan.weekly_review import build_weekly_review
from app.modules.status_collector import collect_all
from tests._demo_seed_qc_helpers import (
    apply_m005,
    apply_through_m007,
    fresh_db,
    qc_seed_snapshot,
)


CITIES = ("montgomery", "fort-worth")
SESSIONS_PER_CITY = 5


@pytest.fixture
def qc_db_path(tmp_path: Path) -> str:
    """DB path with all migrations applied (m001 + m002 + m005 + m006 + m007)."""
    path = fresh_db(tmp_path, name="qc.db")
    apply_m005(path)
    apply_through_m007(path)
    return path


# -------------------- Cycle 7: compliance state --------------------


def test_seed_creates_feedback_token_per_session(qc_db_path: str) -> None:
    """Each demo session has at least one feedback_tokens row (active)."""
    seed_worker_companion_sessions(db_path=qc_db_path)
    conn = sqlite3.connect(qc_db_path)
    try:
        rows = conn.execute(
            "SELECT session_id, COUNT(*) FROM feedback_tokens "
            "GROUP BY session_id"
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) == SESSIONS_PER_CITY * len(CITIES)
    for sid, count in rows:
        assert count >= 1, f"feedback_tokens missing for {sid}"


def test_seed_creates_active_and_expired_feedback_tokens(qc_db_path: str) -> None:
    """At least one session carries an active token AND an expired token."""
    seed_worker_companion_sessions(db_path=qc_db_path)
    now_iso = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(qc_db_path)
    try:
        active = conn.execute(
            "SELECT COUNT(*) FROM feedback_tokens WHERE expires_at > ?",
            (now_iso,),
        ).fetchone()[0]
        expired = conn.execute(
            "SELECT COUNT(*) FROM feedback_tokens WHERE expires_at <= ?",
            (now_iso,),
        ).fetchone()[0]
    finally:
        conn.close()
    assert active >= 1, "no active feedback token seeded"
    assert expired >= 1, "no expired feedback token seeded"


def test_seed_creates_compliance_audit_rows(qc_db_path: str) -> None:
    """Baseline compliance_audit rows exist with hashed session ids."""
    seed_worker_companion_sessions(db_path=qc_db_path)
    conn = sqlite3.connect(qc_db_path)
    try:
        rows = conn.execute(
            "SELECT session_id_hash, action FROM compliance_audit"
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) >= SESSIONS_PER_CITY * len(CITIES)
    actions = {r[1] for r in rows}
    assert "export_requested" in actions, (
        f"expected export_requested action; got {actions}"
    )
    for sid_hash, _action in rows:
        assert len(sid_hash) == 64, f"non-sha256 hash: {sid_hash!r}"
        int(sid_hash, 16)


# -------------------- Cycle 8: weekly review state --------------------


def test_seed_creates_engagement_window_for_each_session(qc_db_path: str) -> None:
    """Every demo session has at least one engagement_events row."""
    seed_worker_companion_sessions(db_path=qc_db_path)
    conn = sqlite3.connect(qc_db_path)
    try:
        rows = conn.execute(
            "SELECT session_id, COUNT(*) FROM engagement_events "
            "WHERE category IN ('digest_sent','reminder_sent', "
            "                   'stall_soft','stall_medium','stall_hard') "
            "GROUP BY session_id"
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) == SESSIONS_PER_CITY * len(CITIES)
    for sid, count in rows:
        assert count >= 1, f"engagement_events missing for {sid}"


def test_weekly_review_returns_nonempty_for_engaged_sessions(
    qc_db_path: str,
) -> None:
    """``build_weekly_review`` produces at least one non-quiet markdown."""
    now = datetime.now(timezone.utc)
    seed_worker_companion_sessions(db_path=qc_db_path, now=now)

    today = now.date()
    window = (today - timedelta(days=7), today)

    conn = sqlite3.connect(qc_db_path)
    try:
        rows = conn.execute("SELECT id FROM sessions").fetchall()
    finally:
        conn.close()

    nonempty = 0
    for (sid,) in rows:
        review = build_weekly_review(sid, window, db_path=qc_db_path)
        if review.engagement_trend.digests_sent > 0:
            nonempty += 1
            assert "Weekly review" in review.summary_markdown
    assert nonempty >= 1, "no session emitted a non-quiet weekly review"


def test_seed_creates_sendgrid_open_for_engaged_sessions(qc_db_path: str) -> None:
    """At least one sendgrid_events 'open' row exists for the heavy sessions."""
    seed_worker_companion_sessions(db_path=qc_db_path)
    conn = sqlite3.connect(qc_db_path)
    try:
        opens = conn.execute(
            "SELECT COUNT(*) FROM sendgrid_events WHERE event_type = 'open'"
        ).fetchone()[0]
    finally:
        conn.close()
    assert opens >= 2, f"expected ≥2 sendgrid open rows, got {opens}"


# -------------------- Cycle 9: advisor inbox state --------------------


def test_seed_creates_one_advisor_token_per_city(qc_db_path: str) -> None:
    """Exactly one advisor_tokens row per city (active, not revoked)."""
    seed_worker_companion_sessions(db_path=qc_db_path)
    conn = sqlite3.connect(qc_db_path)
    try:
        rows = conn.execute(
            "SELECT advisor_id, city, revoked_at FROM advisor_tokens"
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) == len(CITIES), (
        f"expected one advisor token per city; got {len(rows)}"
    )
    cities_seen = {city for _, city, _ in rows}
    assert cities_seen == set(CITIES)
    for advisor_id, city, revoked_at in rows:
        assert revoked_at is None, f"advisor token revoked: {advisor_id}"
        assert city in CITIES


def test_advisor_repository_lists_stalled_sessions_for_each_city(
    qc_db_path: str,
) -> None:
    """The repository excludes demo rows but exposes them when demo=0 flipped."""
    seed_worker_companion_sessions(db_path=qc_db_path)

    for city in CITIES:
        items = advisor_repo.list_stalled_sessions_for_city(qc_db_path, city)
        assert items == [], (
            f"city={city} demo sessions leaked through advisor inbox"
        )

    conn = sqlite3.connect(qc_db_path)
    try:
        conn.execute(
            "UPDATE sessions SET demo = 0 WHERE id IN ("
            "  SELECT s.id FROM sessions s JOIN outcomes_records o "
            "  ON o.session_id = s.id "
            "  WHERE json_extract(o.payload_json,'$.city') = 'montgomery'"
            ")"
        )
        conn.commit()
    finally:
        conn.close()
    items = advisor_repo.list_stalled_sessions_for_city(qc_db_path, "montgomery")
    assert len(items) >= 1, "expected ≥1 stalled session for montgomery"


# -------------------- Cycle 10: reminder state --------------------


def test_seed_creates_reminders_auto_disabled_for_some_sessions(
    qc_db_path: str,
) -> None:
    """At least one session per city has ``reminders_auto_disabled`` set."""
    seed_worker_companion_sessions(db_path=qc_db_path)
    conn = sqlite3.connect(qc_db_path)
    try:
        rows = conn.execute(
            "SELECT DISTINCT session_id FROM engagement_events "
            "WHERE category = 'reminders_auto_disabled'"
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) >= 2, (
        f"expected ≥2 sessions with reminders_auto_disabled, got {len(rows)}"
    )


def test_seed_creates_reminder_cooldowns(qc_db_path: str) -> None:
    """Cooldown rows exist so the cooldown gate has something to check."""
    seed_worker_companion_sessions(db_path=qc_db_path)
    conn = sqlite3.connect(qc_db_path)
    try:
        rows = conn.execute(
            "SELECT category, COUNT(*) FROM reminder_cooldowns GROUP BY category"
        ).fetchall()
    finally:
        conn.close()
    cats = {r[0] for r in rows}
    assert "stall_soft" in cats, "expected stall_soft cooldown row"
    assert "stall_hard" in cats, "expected stall_hard cooldown row"


def test_reminder_engine_status_reports_nonunknown(qc_db_path: str) -> None:
    """``reminder_engine.nightly_status`` is non-``unknown`` for ≥1 session."""
    seed_worker_companion_sessions(db_path=qc_db_path)
    conn = sqlite3.connect(qc_db_path)
    try:
        ids = [r[0] for r in conn.execute("SELECT id FROM sessions").fetchall()]
    finally:
        conn.close()
    healths = {
        reminder_engine.nightly_status(sid, db_path=qc_db_path).health
        for sid in ids
    }
    assert "unknown" not in healths or len(healths) > 1, (
        f"every session reported unknown reminder health: {healths}"
    )


# -------------------- Cycle 11: module-status coverage --------------------


def test_module_status_keys_have_at_least_one_nonunknown_session(
    qc_db_path: str,
) -> None:
    """Every status_collector module reports non-``unknown`` for ≥1 session."""
    seed_worker_companion_sessions(db_path=qc_db_path)
    conn = sqlite3.connect(qc_db_path)
    try:
        ids = [r[0] for r in conn.execute("SELECT id FROM sessions").fetchall()]
    finally:
        conn.close()

    healths_per_module: dict[str, set[str]] = {}
    for sid in ids:
        for status in collect_all(sid, db_path=qc_db_path):
            healths_per_module.setdefault(status.module_name, set()).add(
                status.health,
            )

    missing = [
        module_name for module_name, healths in healths_per_module.items()
        if healths == {"unknown"}
    ]
    assert not missing, (
        f"modules with no non-unknown demo coverage: {missing}; "
        f"all healths: {healths_per_module}"
    )


# -------------------- Cycle 12: determinism + idempotency --------------------


def test_seed_is_deterministic_across_fresh_dbs(tmp_path: Path) -> None:
    """Two fresh DBs seeded with the same ``now`` produce identical payloads."""
    pinned_now = datetime(2026, 4, 24, 12, 0, tzinfo=timezone.utc)

    paths: list[str] = []
    for i in range(2):
        path = fresh_db(tmp_path, name=f"det-{i}.db")
        apply_m005(path)
        apply_through_m007(path)
        seed_worker_companion_sessions(db_path=path, now=pinned_now)
        paths.append(path)

    snapshots = [qc_seed_snapshot(p) for p in paths]
    assert snapshots[0] == snapshots[1], (
        "deterministic seed produced different rows across fresh DBs"
    )


def test_seed_is_idempotent_on_qc_state(qc_db_path: str) -> None:
    """Re-running the seed does not duplicate any QC state row."""
    pinned_now = datetime(2026, 4, 24, 12, 0, tzinfo=timezone.utc)
    seed_worker_companion_sessions(db_path=qc_db_path, now=pinned_now)
    snap1 = qc_seed_snapshot(qc_db_path)
    seed_worker_companion_sessions(db_path=qc_db_path, now=pinned_now)
    snap2 = qc_seed_snapshot(qc_db_path)
    assert snap1 == snap2, "QC seed re-run mutated row payloads"
