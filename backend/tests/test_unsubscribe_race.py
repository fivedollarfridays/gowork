"""Concurrent-unsubscribe idempotency tests (T13.61, S13).

CAN-SPAM Section 5(a)(4) requires that an unsubscribe link work even
under retry — a user who clicks twice (or whose email client
prefetches the URL once and follows it again on click) must NOT see
a 4xx error on the second hit. The MTA may also race the user agent.
The user-visible contract therefore is:

    "Every well-formed valid token returns 200 OK; the opt-out is
    recorded exactly once."

The implementation has two independent atomicity concerns:

1. **used_tokens** — already atomic (INSERT OR IGNORE on
   ``token_hash``), so exactly ONE caller wins the verify race.
2. **engagement_events** — has no unique constraint on
   ``(session_id, category)``, so the route layer must NOT insert a
   second ``reminders_auto_disabled`` row when a duplicate request
   arrives. The fix that satisfies these tests is for the
   ``_process_unsubscribe`` handler to treat ``TokenAlreadyUsed`` as a
   success (return 200 with the same shape) and to refrain from
   re-inserting the opt-out row on the duplicate path.

These tests pin all five guarantees the spec calls out:

* concurrent GETs both return 200 (CAN-SPAM idempotency)
* concurrent POSTs both return 200
* mixed GET+POST both return 200
* sequential replay (>= cooldown window) is still idempotent
* a 10-way burst still produces exactly ONE opt-out + audit row

A ``threading.Barrier`` synchronizes all workers at the dispatch
boundary so the verify race is maximally exposed; the previous
sequential ``test_unsubscribe_get_replay_401`` suite hides it.
"""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import events
from app.core.migrations import runner

from ._fake_clock import freeze_time

_SESSION = "race-sess-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
_FEEDBACK_TOKEN = "race-feedback-tok"
_ADMIN_KEY = "race-admin-key-for-unsubscribe-tests"
_UNSUB_SECRET = "unsub-race-test-secret-0123456789abcdef-xyz"
_SETTINGS_PATCH = "app.core.auth.get_settings"
_FROZEN_INSTANT = "2026-04-24T12:00:00+00:00"


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _isolate_event_bus() -> None:
    events.clear_all_subscribers()
    yield
    events.clear_all_subscribers()


@pytest.fixture(autouse=True)
def _reset_engagement_rate_limit() -> None:
    from app.routes import engagement as eng

    eng._RATE_LIMITER.clear()
    yield
    eng._RATE_LIMITER.clear()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    """Fresh migrated DB seeded with one engagement-tracked session."""
    path = str(tmp_path / "unsubscribe_race.db")
    runner.apply_pending(path)
    _seed_session(path, _SESSION, _FEEDBACK_TOKEN)
    return path


def _seed_session(path: str, session_id: str, token: str) -> None:
    conn = sqlite3.connect(path)
    try:
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        expires_iso = (now + timedelta(days=30)).isoformat()
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, now_iso, "[]", expires_iso),
        )
        conn.execute(
            "INSERT INTO feedback_tokens "
            "(token, session_id, created_at, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (token, session_id, now_iso, expires_iso),
        )
        conn.commit()
    finally:
        conn.close()


def _count_auto_disabled_rows(path: str, session_id: str) -> int:
    conn = sqlite3.connect(path)
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM engagement_events "
            "WHERE session_id = ? AND category = 'reminders_auto_disabled'",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()
    return int(row[0]) if row else 0


@pytest.fixture
def client(db_path: str, monkeypatch) -> TestClient:
    """TestClient against the real FastAPI engagement router."""
    from app.routes import engagement as eng

    monkeypatch.setattr(eng, "_resolve_db_path", lambda: db_path)
    monkeypatch.setenv("UNSUBSCRIBE_TOKEN_SECRET", _UNSUB_SECRET)
    monkeypatch.delenv("UNSUBSCRIBE_TOKEN_SECRET_OLD", raising=False)

    settings_stub = MagicMock()
    settings_stub.admin_api_key = _ADMIN_KEY

    app = FastAPI()
    app.include_router(eng.router)

    with patch(_SETTINGS_PATCH, return_value=settings_stub):
        yield TestClient(app)


def _signed_token(session_id: str = _SESSION) -> str:
    """Sign a fresh unsubscribe token under the test secret."""
    from app.modules.engagement import unsubscribe_tokens

    return unsubscribe_tokens.sign(session_id)


# -------------------- Concurrency harness --------------------


def _run_in_parallel(fns: list) -> list:
    """Run ``fns`` concurrently behind a Barrier; return results in order.

    A Barrier of len(fns) maximizes the race window — every worker is
    blocked at the dispatch line until all are ready, then released
    simultaneously. This exposes any read-then-INSERT non-atomicity
    in the unsubscribe handler.
    """
    barrier = Barrier(len(fns))

    def _wrapped(fn):
        def _runner():
            barrier.wait()
            return fn()
        return _runner

    with ThreadPoolExecutor(max_workers=len(fns)) as pool:
        futures = [pool.submit(_wrapped(fn)) for fn in fns]
        return [f.result(timeout=10) for f in futures]


# -------------------- Test 1: concurrent GETs --------------------


def test_concurrent_get_both_succeed_one_row(
    client: TestClient, db_path: str,
) -> None:
    """Two simultaneous GETs with same token: both 200, one opt-out row."""
    with freeze_time(_FROZEN_INSTANT):
        token = _signed_token()
        url = f"/api/engagement/unsubscribe?token={token}"

        responses = _run_in_parallel(
            [lambda: client.get(url), lambda: client.get(url)],
        )

    statuses = [r.status_code for r in responses]
    assert statuses == [200, 200], (
        f"Both concurrent GETs must succeed (CAN-SPAM idempotency). "
        f"Got: {statuses}; bodies: {[r.text for r in responses]}"
    )
    for resp in responses:
        body = resp.json()
        assert body["session_id"] == _SESSION
        assert body["reminders_enabled"] is False

    assert _count_auto_disabled_rows(db_path, _SESSION) == 1, (
        "Exactly one reminders_auto_disabled row must exist after the race."
    )


# -------------------- Test 2: concurrent POSTs --------------------


def test_concurrent_post_both_succeed_one_row(
    client: TestClient, db_path: str,
) -> None:
    """Two simultaneous POSTs with same token: both 200, one opt-out row."""
    with freeze_time(_FROZEN_INSTANT):
        token = _signed_token()
        body = {"token": token}

        responses = _run_in_parallel([
            lambda: client.post("/api/engagement/unsubscribe", json=body),
            lambda: client.post("/api/engagement/unsubscribe", json=body),
        ])

    statuses = [r.status_code for r in responses]
    assert statuses == [200, 200], (
        f"Both concurrent POSTs must succeed. Got: {statuses}; "
        f"bodies: {[r.text for r in responses]}"
    )
    assert _count_auto_disabled_rows(db_path, _SESSION) == 1


# -------------------- Test 3: mixed GET + POST --------------------


def test_mixed_get_and_post_concurrent(
    client: TestClient, db_path: str,
) -> None:
    """Mixed GET+POST race: both 200, one opt-out row, one audit row."""
    with freeze_time(_FROZEN_INSTANT):
        token = _signed_token()
        get_url = f"/api/engagement/unsubscribe?token={token}"
        post_body = {"token": token}

        responses = _run_in_parallel([
            lambda: client.get(get_url),
            lambda: client.post(
                "/api/engagement/unsubscribe", json=post_body,
            ),
        ])

    statuses = [r.status_code for r in responses]
    assert statuses == [200, 200], (
        f"GET and POST with same token must both succeed. Got: {statuses}; "
        f"bodies: {[r.text for r in responses]}"
    )
    # Opt-out row == audit row (the engagement_events row IS the audit).
    assert _count_auto_disabled_rows(db_path, _SESSION) == 1


# -------------------- Test 4: replay after cooldown window --------------------


def test_replay_after_window_still_idempotent(
    client: TestClient, db_path: str,
) -> None:
    """1st GET, advance 5 min, 2nd GET on same token: both 200, one row.

    The "cooldown window" here is just elapsed wall time — we want to
    prove the idempotency contract is not a coincidence of the verify
    race finishing inside a single tick of the frozen clock. The
    second GET must still succeed and must not insert a second
    opt-out row.
    """
    with freeze_time(_FROZEN_INSTANT) as clock:
        token = _signed_token()
        url = f"/api/engagement/unsubscribe?token={token}"

        first = client.get(url)
        clock.advance(timedelta(minutes=5))
        second = client.get(url)

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert _count_auto_disabled_rows(db_path, _SESSION) == 1


# -------------------- Test 5: 10-way burst --------------------


def test_burst_n_concurrent_one_row(
    client: TestClient, db_path: str,
) -> None:
    """10 concurrent GETs with same token: all 200, one opt-out row total."""
    n = 10
    with freeze_time(_FROZEN_INSTANT):
        token = _signed_token()
        url = f"/api/engagement/unsubscribe?token={token}"

        responses = _run_in_parallel(
            [lambda url=url: client.get(url) for _ in range(n)],
        )

    statuses = [r.status_code for r in responses]
    assert statuses == [200] * n, (
        f"All {n} concurrent GETs must succeed. Got: {statuses}"
    )
    assert _count_auto_disabled_rows(db_path, _SESSION) == 1, (
        "10-way burst must produce exactly one reminders_auto_disabled row."
    )
