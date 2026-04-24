"""Route + dependency tests for the advisor inbox (T12.31).

Covers the three ``/api/advisor/*`` endpoints end-to-end plus the
cross-cutting policy guarantees from section 10 of
``docs/security/advisor-auth.md``:

* Uniform 401 on any auth failure (missing row / revoked row).
* City-scoped list response — cross-city sessions never leak.
* Demo sessions excluded (``sessions.demo`` filter).
* Sorted by stall severity DESC then days DESC.
* Cross-city detail access → HTTP **403** (not 404, not empty).
* Send-note dispatches through ``reminder_engine.send_advisor_note``.
* Send-note rate-limited at 3/hour per advisor → 429.
* Every advisor action writes an ``engagement_events`` row with
  ``category='advisor_action'`` and a SHA256-hashed advisor id.

Migration + token-helper tests live in ``test_advisor_auth.py``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.migrations import runner
from tests._advisor_helpers import (
    _SID_FW_1,
    _SID_MTG_1,
    _SID_MTG_2,
    _SID_NOTE,
    _SID_RATE,
    _SID_DEMO,
    _SID_REAL,
    _TOKEN,
    build_client,
    insert_advisor_token,
    read_advisor_action_rows,
    seed_stalled_session,
    stub_send_advisor_note,
)


@pytest.fixture
def migrated_db(tmp_path: Path) -> str:
    """Temp DB with the full migration chain (through m007)."""
    db_path = str(tmp_path / "advisor_inbox.db")
    runner.apply_pending(db_path)
    return db_path


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> None:
    """Reset the per-advisor rate limiter between tests."""
    from app.routes import advisor_inbox
    advisor_inbox._RATE_LIMITER.clear()


# ---------------------------------------------------------------- auth


def test_stalled_sessions_requires_valid_token(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing / unknown token → 401 with the uniform body."""
    client = build_client(migrated_db, monkeypatch)
    r = client.get(
        "/api/advisor/stalled-sessions",
        headers={"X-Admin-Key": "mw_adv_bogus"},
    )
    assert r.status_code == 401
    assert r.json() == {"detail": "Invalid advisor token"}


def test_stalled_sessions_revoked_returns_401(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Revoked token → 401 with identical body (no enumeration)."""
    insert_advisor_token(
        migrated_db, _TOKEN, "adv-jane", "montgomery", revoked=True,
    )
    client = build_client(migrated_db, monkeypatch)
    r = client.get(
        "/api/advisor/stalled-sessions",
        headers={"X-Admin-Key": _TOKEN},
    )
    assert r.status_code == 401
    assert r.json() == {"detail": "Invalid advisor token"}


# ---------------------------------------------------------------- list


def test_stalled_sessions_happy_path_returns_scoped_list(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Advisor for montgomery sees only montgomery sessions."""
    insert_advisor_token(
        migrated_db, _TOKEN, "adv-jane", "montgomery",
    )
    seed_stalled_session(migrated_db, _SID_MTG_1, "montgomery", days_ago=30)
    seed_stalled_session(migrated_db, _SID_FW_1, "fort-worth", days_ago=30)
    client = build_client(migrated_db, monkeypatch)
    r = client.get(
        "/api/advisor/stalled-sessions",
        headers={"X-Admin-Key": _TOKEN},
    )
    assert r.status_code == 200, r.text
    ids = [s["session_id"] for s in r.json()["sessions"]]
    assert _SID_MTG_1 in ids
    assert _SID_FW_1 not in ids


def test_stalled_sessions_excludes_demo(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Demo-flagged sessions do not surface in advisor views."""
    insert_advisor_token(
        migrated_db, _TOKEN, "adv-jane", "montgomery",
    )
    seed_stalled_session(
        migrated_db, _SID_DEMO, "montgomery", days_ago=30, demo=True,
    )
    seed_stalled_session(
        migrated_db, _SID_REAL, "montgomery", days_ago=30,
    )
    client = build_client(migrated_db, monkeypatch)
    r = client.get(
        "/api/advisor/stalled-sessions",
        headers={"X-Admin-Key": _TOKEN},
    )
    ids = [s["session_id"] for s in r.json()["sessions"]]
    assert _SID_REAL in ids
    assert _SID_DEMO not in ids


def test_stalled_sessions_sorted_by_severity_then_days(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HARD (>=15d) before MEDIUM (>=7d) before SOFT (>=3d)."""
    insert_advisor_token(
        migrated_db, _TOKEN, "adv-jane", "montgomery",
    )
    sid_soft = "a0000000-0000-4000-8000-000000000001"
    sid_hard_9 = "a0000000-0000-4000-8000-000000000002"
    sid_hard_30 = "a0000000-0000-4000-8000-000000000003"
    sid_medium = "a0000000-0000-4000-8000-000000000004"
    seed_stalled_session(migrated_db, sid_soft, "montgomery", days_ago=4)
    seed_stalled_session(migrated_db, sid_hard_9, "montgomery", days_ago=20)
    seed_stalled_session(migrated_db, sid_hard_30, "montgomery", days_ago=30)
    seed_stalled_session(migrated_db, sid_medium, "montgomery", days_ago=10)
    client = build_client(migrated_db, monkeypatch)
    r = client.get(
        "/api/advisor/stalled-sessions",
        headers={"X-Admin-Key": _TOKEN},
    )
    ids = [s["session_id"] for s in r.json()["sessions"]]
    assert ids[0] == sid_hard_30
    assert ids[1] == sid_hard_9
    assert ids[2] == sid_medium
    assert ids[3] == sid_soft


# ---------------------------------------------------------------- detail


def test_session_detail_happy_path(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """In-city detail call returns 200 with the session body."""
    insert_advisor_token(
        migrated_db, _TOKEN, "adv-jane", "montgomery",
    )
    seed_stalled_session(
        migrated_db, _SID_MTG_2, "montgomery", days_ago=10,
    )
    client = build_client(migrated_db, monkeypatch)
    r = client.get(
        f"/api/advisor/sessions/{_SID_MTG_2}",
        headers={"X-Admin-Key": _TOKEN},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["session_id"] == _SID_MTG_2
    assert body["city"] == "montgomery"


def test_session_detail_cross_city_returns_403(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cross-city detail call must return 403 — NOT 404, NOT empty."""
    insert_advisor_token(
        migrated_db, _TOKEN, "adv-jane", "montgomery",
    )
    seed_stalled_session(migrated_db, _SID_FW_1, "fort-worth", days_ago=10)
    client = build_client(migrated_db, monkeypatch)
    r = client.get(
        f"/api/advisor/sessions/{_SID_FW_1}",
        headers={"X-Admin-Key": _TOKEN},
    )
    assert r.status_code == 403, r.text
    assert r.json() == {"detail": "Cross-city access denied"}


# ---------------------------------------------------------------- send-note


def test_send_note_calls_reminder_engine_and_audits(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /sessions/{id}/note goes through reminder_engine.send_advisor_note."""
    insert_advisor_token(
        migrated_db, _TOKEN, "adv-jane", "montgomery",
    )
    seed_stalled_session(
        migrated_db, _SID_NOTE, "montgomery", days_ago=10,
    )
    calls: list[dict] = []
    stub_send_advisor_note(monkeypatch, calls)
    client = build_client(migrated_db, monkeypatch)
    r = client.post(
        f"/api/advisor/sessions/{_SID_NOTE}/note",
        headers={"X-Admin-Key": _TOKEN},
        json={"message": "Hey — give me a call when you can."},
    )
    assert r.status_code == 200, r.text
    assert calls and calls[0]["session_id"] == _SID_NOTE
    assert "Hey" in calls[0]["message"]
    payloads = read_advisor_action_rows(migrated_db, _SID_NOTE)
    assert len(payloads) == 1
    payload = payloads[0]
    assert payload["action"] == "send_note"
    assert payload["city"] == "montgomery"
    assert "advisor_id_hash" in payload
    assert payload["advisor_id_hash"] != "adv-jane"  # hashed, not raw


def test_send_note_cross_city_returns_403(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Note POST to a cross-city session returns 403."""
    insert_advisor_token(
        migrated_db, _TOKEN, "adv-jane", "montgomery",
    )
    seed_stalled_session(migrated_db, _SID_FW_1, "fort-worth", days_ago=10)
    client = build_client(migrated_db, monkeypatch)
    r = client.post(
        f"/api/advisor/sessions/{_SID_FW_1}/note",
        headers={"X-Admin-Key": _TOKEN},
        json={"message": "hi"},
    )
    assert r.status_code == 403


def test_send_note_rate_limited_at_three_per_hour(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fourth send-note in the same hour → 429."""
    insert_advisor_token(
        migrated_db, _TOKEN, "adv-jane", "montgomery",
    )
    seed_stalled_session(migrated_db, _SID_RATE, "montgomery", days_ago=10)
    stub_send_advisor_note(monkeypatch)
    client = build_client(migrated_db, monkeypatch)
    for _ in range(3):
        r = client.post(
            f"/api/advisor/sessions/{_SID_RATE}/note",
            headers={"X-Admin-Key": _TOKEN},
            json={"message": "ping"},
        )
        assert r.status_code == 200
    r = client.post(
        f"/api/advisor/sessions/{_SID_RATE}/note",
        headers={"X-Admin-Key": _TOKEN},
        json={"message": "ping"},
    )
    assert r.status_code == 429


# ---------------------------------------------------------------- audit


def test_list_writes_audit_row(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Even GET /stalled-sessions writes an advisor_action audit row."""
    insert_advisor_token(
        migrated_db, _TOKEN, "adv-jane", "montgomery",
    )
    client = build_client(migrated_db, monkeypatch)
    r = client.get(
        "/api/advisor/stalled-sessions",
        headers={"X-Admin-Key": _TOKEN},
    )
    assert r.status_code == 200
    # Listing audit lives under the placeholder session id.
    payloads = read_advisor_action_rows(
        migrated_db, "_advisor_audit",
    )
    assert len(payloads) == 1
    payload = payloads[0]
    assert payload["action"] == "list_stalled_sessions"
    assert payload["city"] == "montgomery"
