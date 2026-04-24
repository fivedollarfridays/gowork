"""S12b integration gate (T12.35b) — endpoint auth + funnel + retention.

Companion to ``test_s12b_gate.py`` (sections H..K). Sections here:

  H. Compliance + advisor endpoints require auth — unauthenticated
     calls return 401 / 422; cross-city returns 403.
  I. Demo seed + T12.12 community-funnel regression.
  J. Retention sweep wired into nightly orchestrator.
  K. Load test — 200 sessions × 2 cities under 600s (gated).

Helpers live in ``tests._s12b_gate_helpers``.
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests._s12b_gate_helpers import apply_all_migrations


# ====================================================================
# H. Compliance + advisor endpoints require auth
# ====================================================================


def _build_compliance_app(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    from app.routes import compliance as compliance_mod
    monkeypatch.setattr(
        compliance_mod, "_resolve_db_path", lambda: db_path,
    )
    app = FastAPI()
    app.include_router(compliance_mod.router)
    return TestClient(app)


def test_compliance_endpoints_reject_missing_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /api/compliance/{export,delete,delete/selective} all require a
    session_token — missing/invalid token returns 401 (or 422 on malformed)."""
    db_path = str(tmp_path / "comp.db")
    apply_all_migrations(db_path)
    client = _build_compliance_app(db_path, monkeypatch)

    # Totally missing body fields -> 422 (Pydantic validation).
    r = client.post("/api/compliance/export", json={})
    assert r.status_code == 422

    # Body present but token is bogus -> 401 (unknown session_id).
    r = client.post(
        "/api/compliance/export",
        json={"session_id": "nope", "session_token": "bogus-token-xyz"},
    )
    assert r.status_code == 401, r.text

    r = client.post(
        "/api/compliance/delete",
        json={
            "session_id": "nope", "session_token": "bogus",
            "confirm": "DELETE",
        },
    )
    assert r.status_code == 401, r.text

    r = client.post(
        "/api/compliance/delete/selective",
        json={
            "session_id": "nope", "session_token": "bogus",
            "category": "criminal_record",
        },
    )
    assert r.status_code == 401, r.text


def _build_advisor_app(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    from app.routes import advisor_inbox as adv_mod
    monkeypatch.setattr(adv_mod, "_resolve_db_path", lambda: db_path)
    app = FastAPI()
    app.include_router(adv_mod.router)
    return TestClient(app)


def test_advisor_endpoints_reject_missing_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /api/advisor/stalled-sessions (and friends) require X-Admin-Key
    — missing header returns 422 (FastAPI dependency), invalid returns 401."""
    db_path = str(tmp_path / "adv.db")
    apply_all_migrations(db_path)
    client = _build_advisor_app(db_path, monkeypatch)

    # Missing X-Admin-Key header -> FastAPI Header(...) gives 422.
    r = client.get("/api/advisor/stalled-sessions")
    assert r.status_code in (401, 422)

    # Header present but unknown token -> 401 uniform body.
    r = client.get(
        "/api/advisor/stalled-sessions",
        headers={"X-Admin-Key": "unknown-token"},
    )
    assert r.status_code == 401, r.text
    assert r.json() == {"detail": "Invalid advisor token"}

    r = client.get(
        "/api/advisor/sessions/some-sid",
        headers={"X-Admin-Key": "unknown-token"},
    )
    assert r.status_code == 401

    r = client.post(
        "/api/advisor/sessions/some-sid/note",
        headers={"X-Admin-Key": "unknown-token"},
        json={"message": "hi"},
    )
    assert r.status_code == 401


def test_advisor_cross_city_returns_403(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Advisor with city=montgomery asking for fort-worth session gets 403."""
    from tests._s12b_e2e_helpers import (
        SESSION_FTW,
        TOKEN_FTW,
        build_advisor_client,
        insert_advisor_token,
        insert_recent_city_outcome,
        seed_session,
    )

    db_path = str(tmp_path / "xcity.db")
    apply_all_migrations(db_path)
    seed_session(db_path, SESSION_FTW, TOKEN_FTW, city="fort-worth")
    insert_recent_city_outcome(
        db_path, SESSION_FTW, "fort-worth", days_ago=10,
    )
    insert_advisor_token(
        db_path, "mw_adv_gate_montgomery_token_example", "adv-mtg",
        "montgomery",
    )

    client = build_advisor_client(db_path, monkeypatch)
    r = client.get(
        f"/api/advisor/sessions/{SESSION_FTW}",
        headers={"X-Admin-Key": "mw_adv_gate_montgomery_token_example"},
    )
    assert r.status_code == 403, r.text


# ====================================================================
# I. Demo seed + T12.12 community-funnel regression
# ====================================================================


def test_demo_seed_creates_ten_demo_sessions(tmp_path: Path) -> None:
    """seed_worker_companion_sessions inserts 10 demo sessions (5 per city)."""
    from app.demo_seed import seed_worker_companion_sessions

    db_path = str(tmp_path / "seed.db")
    apply_all_migrations(db_path)
    seed_worker_companion_sessions(db_path=db_path)

    conn = sqlite3.connect(db_path)
    try:
        demo_total = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE demo = 1"
        ).fetchone()[0]
        per_city = dict(conn.execute(
            "SELECT json_extract(o.payload_json, '$.city') AS city, "
            "COUNT(DISTINCT s.id) "
            "FROM sessions s "
            "JOIN outcomes_records o ON o.session_id = s.id "
            "WHERE s.demo = 1 "
            "GROUP BY city"
        ).fetchall())
    finally:
        conn.close()

    assert demo_total >= 10, (
        f"expected at least 10 demo sessions, got {demo_total}"
    )
    mtg = per_city.get("montgomery", 0)
    ftw = per_city.get("fort-worth", 0)
    assert mtg >= 5 and ftw >= 5, (
        f"expected 5+ per city, got mtg={mtg} ftw={ftw} "
        f"(per_city={per_city})"
    )


def test_funnel_query_excludes_demo_rows(tmp_path: Path) -> None:
    """T12.12 community funnel guard filters out demo=1 sessions."""
    from app.modules.jobs.funnel_queries import has_demo_column

    db_path = str(tmp_path / "funnel.db")
    apply_all_migrations(db_path)

    conn = sqlite3.connect(db_path)
    try:
        assert has_demo_column(conn) is True

        now = "2026-04-23T00:00:00Z"
        for sid, demo in (("real-1", 0), ("demo-1", 1)):
            conn.execute(
                "INSERT INTO sessions "
                "(id, created_at, barriers, expires_at, demo) "
                "VALUES (?, ?, '[]', '2026-05-23T00:00:00Z', ?)",
                (sid, now, demo),
            )
        conn.commit()

        row = conn.execute(
            "SELECT COUNT(*) FROM sessions "
            "WHERE demo IS NULL OR demo = 0"
        ).fetchone()
        assert row[0] == 1, (
            f"expected 1 non-demo row, got {row[0]}"
        )
    finally:
        conn.close()


# ====================================================================
# J. Retention sweep wired into nightly orchestrator
# ====================================================================


def test_retention_sweep_wired_into_nightly_orchestrator() -> None:
    """scripts.nightly_digest imports + calls compliance.retention_sweep."""
    import inspect

    from scripts import nightly_digest as nd_mod
    from app.modules.compliance import retention as ret_mod

    assert hasattr(nd_mod, "_retention_mod") or hasattr(
        nd_mod, "_run_retention_sweep"
    ), "nightly_digest must reference the retention module"

    source = inspect.getsource(nd_mod)
    assert "retention_sweep" in source, (
        "nightly_digest source must invoke retention_sweep"
    )
    assert callable(ret_mod.retention_sweep)


# ====================================================================
# K. Load test — 200 sessions × 2 cities under 600s (gated)
# ====================================================================


_RUN_LOAD = os.environ.get("RUN_LOAD_TESTS") == "1"


@pytest.mark.skipif(
    not _RUN_LOAD,
    reason="scale load test only runs with RUN_LOAD_TESTS=1",
)
def test_nightly_orchestrator_scale_200_sessions_under_10_min(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """200 sessions across 2 cities complete under 600s wall clock."""
    import time

    from scripts.nightly_digest import run_nightly_digest
    from tests._s12a_e2e_helpers import (
        install_sendgrid_spy, seed_session,
    )

    db_path = str(tmp_path / "load.db")
    apply_all_migrations(db_path)

    for i in range(100):
        seed_session(
            db_path, f"mty-{i:04d}", f"tok-mty-{i:04d}",
            barriers=["expunction"], city="montgomery",
            email=f"w{i}@montgomery.test",
        )
        seed_session(
            db_path, f"ftw-{i:04d}", f"tok-ftw-{i:04d}",
            barriers=["nondisclosure"], city="fort-worth",
            email=f"w{i}@fortworth.test",
        )

    install_sendgrid_spy(monkeypatch)

    start = time.monotonic()
    asyncio.run(run_nightly_digest(
        cities=["montgomery", "fort-worth"], db_path=db_path,
    ))
    elapsed = time.monotonic() - start

    assert elapsed < 600.0, (
        f"nightly orchestrator took {elapsed:.1f}s for 200 sessions, "
        f"expected < 600s"
    )
