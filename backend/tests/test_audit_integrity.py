"""Audit-row integrity + ordering for every mutating endpoint (T13.59).

The contract under test
=======================

For every mutating API endpoint that writes a DB audit row, this suite
verifies four properties in turn:

1. **Coverage** — every mutating route the FastAPI app exposes is
   triaged into either ``EXPECTED_AUDIT_SHAPES`` (writes one audit row)
   or ``AUDIT_ALLOWLIST`` (intentionally not a DB-row writer, with a
   one-line rationale). See :mod:`tests._audit_integrity_fixtures`.

2. **One row per call** — for every entry in ``EXPECTED_AUDIT_SHAPES``,
   a successful call grows the named audit table by exactly one row.
   The delta is checked against a pre-call count + filter so a writer
   that double-writes (or silently skips) is caught immediately.

3. **Audit-before-build ordering** — the compliance download flow
   established the pattern in S12b commit 4c8207a: ``write_audit
   (export_downloaded)`` fires BEFORE the (potentially failing)
   archive build, and a second ``write_audit(export_failed)`` row is
   written when the build raises. This suite locks that pattern in by
   monkeypatching the build step to raise and asserting both rows
   land — even though the response is a 500.

4. **Idempotency / no double-audit on retry** — for endpoints whose
   auth gate atomically consumes a single-use token (unsubscribe), a
   replayed request rejects with 401 AND writes no second audit row.

5. **No raw PII in audit rows** — every audit table is scanned after
   the call for leaked emails, raw session ids, and raw advisor ids.
   ``compliance_audit`` MUST hash the session id; ``engagement_events``
   payload MUST hash the advisor id (the table's own session_id
   column is a NOT NULL FK and is intentionally raw).

The CLI ``bypass_log.jsonl`` (under ``.paircoder/history/``) is a
JSONL file maintained by the bpsai-pair toolchain, NOT a runtime
audit sink the FastAPI app writes to. It is intentionally out of
scope here.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.core.migrations import runner
from tests._audit_integrity_drivers import (
    ADMIN_KEY,
    ADVISOR_ID,
    COMPLIANCE_SECRET,
    DEFAULT_SESSION_ID,
    DRIVERS,
    UNSUB_SECRET,
    WORKER_FIRST_NAME,
    build_where,
    ctx_default,
    drive_compliance_delete,
    drive_compliance_export,
    iteration_context,
    row_count,
    seed_advisor_token,
    seed_session_and_token,
)
from tests._audit_integrity_fixtures import (
    AUDIT_ALLOWLIST,
    EXPECTED_AUDIT_SHAPES,
)


# --------------------------------------------------------------- fixtures


@pytest.fixture
def audit_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Migrated SQLite DB seeded with the canonical worker + advisor."""
    db_path = str(tmp_path / "audit_integrity.db")
    runner.apply_pending(db_path)
    seed_session_and_token(db_path)
    seed_advisor_token(db_path)
    monkeypatch.setenv("UNSUBSCRIBE_TOKEN_SECRET", UNSUB_SECRET)
    monkeypatch.setenv("COMPLIANCE_TOKEN_SECRET", COMPLIANCE_SECRET)
    monkeypatch.delenv("UNSUBSCRIBE_TOKEN_SECRET_OLD", raising=False)
    monkeypatch.delenv("COMPLIANCE_TOKEN_SECRET_OLD", raising=False)
    return db_path


@pytest.fixture
def audit_app(
    audit_db: str, monkeypatch: pytest.MonkeyPatch,
) -> FastAPI:
    """FastAPI app mounted with every router whose endpoints are tested.

    Avoids importing :mod:`app.main` so the test does not pull in the
    SQLAlchemy engine / async startup hooks. The test only needs the
    sync routers that own audit-writing endpoints.
    """
    from app.routes import advisor_inbox, compliance, engagement, admin_flags

    monkeypatch.setattr(
        compliance, "_resolve_db_path", lambda: audit_db,
    )
    monkeypatch.setattr(
        engagement, "_resolve_db_path", lambda: audit_db,
    )
    monkeypatch.setattr(
        advisor_inbox, "_resolve_db_path", lambda: audit_db,
    )
    compliance._RATE_LIMITER.clear()
    engagement._RATE_LIMITER.clear()
    advisor_inbox._RATE_LIMITER.clear()
    from app.core import feature_flags as ff_mod
    ff_mod._reset_state_for_tests()

    settings_stub = MagicMock()
    settings_stub.admin_api_key = ADMIN_KEY
    settings_stub.database_url = f"sqlite+aiosqlite:///{audit_db}"
    monkeypatch.setattr(
        "app.core.auth.get_settings", lambda: settings_stub,
    )
    monkeypatch.setattr(
        "app.core.feature_flags.get_settings", lambda: settings_stub,
    )

    app = FastAPI()
    app.include_router(compliance.router)
    app.include_router(engagement.router)
    app.include_router(advisor_inbox.router)
    app.include_router(admin_flags.router)
    return app


@pytest.fixture
def audit_client(audit_app: FastAPI) -> TestClient:
    """TestClient that does not raise server exceptions (ordering test needs 500s)."""
    return TestClient(audit_app, raise_server_exceptions=False)


# --------------------------------------------------------------- inventory


def _live_mutating_routes() -> set[str]:
    """Return ``{'METHOD path'}`` for every mutating route in the live app."""
    from app.main import app

    out: set[str] = set()
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in sorted(route.methods or ()):
            if method in {"GET", "HEAD", "OPTIONS"}:
                continue
            out.add(f"{method} {route.path}")
    # Two GET-shaped writes are part of the audit contract (CAN-SPAM
    # unsubscribe). They must round-trip through the same triage.
    out.add("GET /api/engagement/unsubscribe")
    return out


# --------------------------------------------------------------- coverage guard


def test_every_mutating_endpoint_is_triaged() -> None:
    """Every mutating route must be in EXPECTED_AUDIT_SHAPES or AUDIT_ALLOWLIST.

    Catches forgotten audit calls before they ship — a contributor
    adding a new mutating endpoint must commit to one of two
    statements: "this writes audit row X" or "this is intentionally
    not a DB-audit-row writer, here's why".
    """
    live = _live_mutating_routes()
    triaged = set(EXPECTED_AUDIT_SHAPES) | set(AUDIT_ALLOWLIST)
    untriaged = sorted(live - triaged)
    assert not untriaged, (
        "New mutating endpoints lack an audit-integrity decision — "
        "either add an EXPECTED_AUDIT_SHAPES entry (writes a DB row) "
        "or an AUDIT_ALLOWLIST entry (with rationale):\n"
        + "\n".join(untriaged)
    )


def test_no_audit_shape_for_missing_route() -> None:
    """EXPECTED_AUDIT_SHAPES + AUDIT_ALLOWLIST must reference real routes."""
    live = _live_mutating_routes()
    declared = set(EXPECTED_AUDIT_SHAPES) | set(AUDIT_ALLOWLIST)
    stale = sorted(declared - live)
    assert not stale, (
        f"Audit-integrity tables reference routes that no longer "
        f"exist: {stale}"
    )


def test_audit_shape_and_allowlist_are_disjoint() -> None:
    """A route is either expected-to-audit OR allowlisted, never both."""
    overlap = sorted(set(EXPECTED_AUDIT_SHAPES) & set(AUDIT_ALLOWLIST))
    assert not overlap, (
        f"Routes in both audit shapes and allowlist: {overlap}"
    )


def test_every_audit_shape_has_a_driver() -> None:
    """Every EXPECTED_AUDIT_SHAPES key must have a request driver."""
    missing = sorted(set(EXPECTED_AUDIT_SHAPES) - set(DRIVERS))
    assert not missing, (
        f"EXPECTED_AUDIT_SHAPES keys without a driver: {missing}"
    )


# --------------------------------------------------------------- single-row test


def _exercise_one_endpoint(
    audit_client: TestClient, audit_db: str,
    monkeypatch: pytest.MonkeyPatch, idx: int, endpoint: str,
) -> str | None:
    """Run one endpoint's driver and return a failure string (or None)."""
    shape = EXPECTED_AUDIT_SHAPES[endpoint]
    ctx = iteration_context(idx)
    seed_session_and_token(
        audit_db,
        session_id=ctx.session_id, feedback_token=ctx.feedback_token,
    )
    where = build_where(shape, session_id=ctx.session_id)
    before = row_count(audit_db, shape.table, where)
    driver = DRIVERS[endpoint]
    try:
        if endpoint == "POST /api/advisor/sessions/{session_id}/note":
            response = driver(audit_client, ctx, monkeypatch)
        else:
            response = driver(audit_client, ctx)
    except Exception as exc:  # noqa: BLE001
        return f"{endpoint}: driver raised {type(exc).__name__}: {exc}"
    if response.status_code >= 400:
        return (
            f"{endpoint}: driver got {response.status_code} "
            f"body={response.text[:200]!r}"
        )
    after = row_count(audit_db, shape.table, where)
    delta = after - before
    if delta != 1:
        return (
            f"{endpoint}: expected exactly 1 audit row in "
            f"{shape.table} ({where or 'no filter'}), got delta={delta}"
        )
    return None


def test_every_mutating_endpoint_writes_exactly_one_audit_row(
    audit_client: TestClient, audit_db: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """For every audit-shape entry: one successful call -> +1 row.

    Snapshot count(*) (filtered by category/action/session), fire the
    request, snapshot count(*) again, assert delta == 1. A delta of 0
    means the route silently skipped its audit; a delta of 2+ means a
    double-write (the failure mode T13.59 was scheduled to catch).
    """
    failures: list[str] = []
    for idx, endpoint in enumerate(EXPECTED_AUDIT_SHAPES):
        failure = _exercise_one_endpoint(
            audit_client, audit_db, monkeypatch, idx, endpoint,
        )
        if failure is not None:
            failures.append(failure)
    assert not failures, (
        "Audit-row integrity broken on the following endpoints:\n"
        + "\n".join(failures)
    )


# --------------------------------------------------------------- ordering test


def _setup_failing_build(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force ``compliance.export.build_archive`` to raise."""
    from app.modules.compliance import export as export_mod

    def _failing_build(*args: Any, **kwargs: Any) -> bytes:
        raise RuntimeError("build failure simulated by audit-integrity test")

    monkeypatch.setattr(export_mod, "build_archive", _failing_build)


def test_audit_before_build_ordering_compliance_download(
    audit_client: TestClient, audit_db: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The compliance download writes audit BEFORE attempting the build.

    Locks in the pattern established by S12b commit 4c8207a:

        write_audit(action="export_downloaded")    # FIRST
        try:
            build_archive(...)                     # might raise
        except Exception as exc:
            write_audit(action="export_failed",     # SECOND
                        payload={"error_class": ...})
            raise

    Proof: monkeypatch ``build_archive`` to raise, fire the download
    request, then assert BOTH ``export_downloaded`` and
    ``export_failed`` rows exist. A regression where audit lands AFTER
    build would leak no rows on failure.
    """
    from app.modules.compliance import _export_tokens

    download_token = _export_tokens.sign_export_token(
        DEFAULT_SESSION_ID, archive_id="audit-integrity-archive",
    )
    _setup_failing_build(monkeypatch)
    before_d = row_count(
        audit_db, "compliance_audit", "action = 'export_downloaded'",
    )
    before_f = row_count(
        audit_db, "compliance_audit", "action = 'export_failed'",
    )
    response = audit_client.get(
        f"/api/compliance/export/download?token={download_token}",
    )
    assert response.status_code == 500, response.text
    after_d = row_count(
        audit_db, "compliance_audit", "action = 'export_downloaded'",
    )
    after_f = row_count(
        audit_db, "compliance_audit", "action = 'export_failed'",
    )
    assert after_d - before_d == 1, (
        "export_downloaded audit row did NOT land before the build "
        "step — the audit-before-build ordering is broken."
    )
    assert after_f - before_f == 1, (
        "export_failed audit row did NOT land after the build raised."
    )


# --------------------------------------------------------------- idempotency


def _replay_unsubscribe(
    audit_client: TestClient, *, method: str,
) -> tuple[int, int]:
    """Sign one token, send it twice, return (status1, status2)."""
    from app.modules.engagement import unsubscribe_tokens

    token = unsubscribe_tokens.sign(DEFAULT_SESSION_ID)
    if method == "POST":
        first = audit_client.post(
            "/api/engagement/unsubscribe", json={"token": token},
        )
        second = audit_client.post(
            "/api/engagement/unsubscribe", json={"token": token},
        )
    else:
        first = audit_client.get(
            f"/api/engagement/unsubscribe?token={token}",
        )
        second = audit_client.get(
            f"/api/engagement/unsubscribe?token={token}",
        )
    return first.status_code, second.status_code


def test_idempotent_unsubscribe_does_not_double_audit(
    audit_client: TestClient, audit_db: str,
) -> None:
    """Replaying an unsubscribe token writes exactly one audit row total.

    Updated for T13.61 — CAN-SPAM Section 5(a)(4) requires replay to
    return 200 (not 401), but the *audit invariant* this test guards
    is unchanged: the second write to ``engagement_events`` must NOT
    fire. The atomic INSERT into ``used_tokens`` (the single-use guard)
    routes the second call through the idempotent-replay branch, which
    skips the duplicate audit row. A regression here would look like:
    the audit write fires BEFORE the dedup guard, so two audit rows
    land before the replay branch is reached.
    """
    where = (
        "category = 'reminders_auto_disabled' "
        f"AND session_id = '{DEFAULT_SESSION_ID}'"
    )
    before = row_count(audit_db, "engagement_events", where)
    s1, s2 = _replay_unsubscribe(audit_client, method="POST")
    assert s1 == 200 and s2 == 200, f"got ({s1}, {s2})"
    after = row_count(audit_db, "engagement_events", where)
    assert after - before == 1, (
        f"Idempotent retry double-audited: delta={after - before}"
    )


def test_idempotent_unsubscribe_get_does_not_double_audit(
    audit_client: TestClient, audit_db: str,
) -> None:
    """GET (CAN-SPAM) handler is idempotent — replay -> 200, one audit row.

    Updated for T13.61. The MTA + MUA combo can issue a prefetch GET
    followed by a real GET on the same URL; both must succeed and
    only one ``reminders_auto_disabled`` row may land.
    """
    where = (
        "category = 'reminders_auto_disabled' "
        f"AND session_id = '{DEFAULT_SESSION_ID}'"
    )
    before = row_count(audit_db, "engagement_events", where)
    s1, s2 = _replay_unsubscribe(audit_client, method="GET")
    assert s1 == 200 and s2 == 200, f"got ({s1}, {s2})"
    after = row_count(audit_db, "engagement_events", where)
    assert after - before == 1


# --------------------------------------------------------------- PII test


_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
)


def _scan_table_for_pii(
    db_path: str, table: str, columns: tuple[str, ...],
    raw_session_ids: set[str], advisor_id: str,
) -> list[str]:
    """Return human-readable findings for every PII leak in ``table``."""
    cols = ", ".join(columns)
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(f"SELECT {cols} FROM {table}").fetchall()
    finally:
        conn.close()
    findings: list[str] = []
    for row in rows:
        joined = " ".join(str(v) if v is not None else "" for v in row)
        if _EMAIL_RE.search(joined):
            findings.append(f"{table}: row contains an email address")
        if any(sid in joined for sid in raw_session_ids):
            findings.append(
                f"{table}: row contains raw session_id (must be hashed)",
            )
        if WORKER_FIRST_NAME in joined:
            findings.append(f"{table}: row contains worker first name")
        if advisor_id in joined:
            findings.append(
                f"{table}: row contains raw advisor_id (must be hashed)",
            )
    return findings


def _exercise_all_drivers_for_pii(
    audit_client: TestClient, audit_db: str,
    monkeypatch: pytest.MonkeyPatch,
) -> set[str]:
    """Run every driver once; return the set of session ids used."""
    used: set[str] = set()
    for idx, (endpoint, driver) in enumerate(DRIVERS.items()):
        ctx = iteration_context(idx)
        used.add(ctx.session_id)
        seed_session_and_token(
            audit_db,
            session_id=ctx.session_id, feedback_token=ctx.feedback_token,
        )
        if endpoint == "POST /api/advisor/sessions/{session_id}/note":
            driver(audit_client, ctx, monkeypatch)
        else:
            driver(audit_client, ctx)
    return used


def test_audit_rows_contain_no_pii(
    audit_client: TestClient, audit_db: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After every endpoint fires, no audit row carries raw PII.

    PII = email address, raw session_id (in tables that should hash
    it), worker first name, raw advisor_id. ``engagement_events``
    intentionally stores the raw session_id in its FK column; the
    scan there only inspects ``category`` and ``payload_json``.
    """
    used_sids = _exercise_all_drivers_for_pii(
        audit_client, audit_db, monkeypatch,
    )
    findings: list[str] = []
    findings.extend(_scan_table_for_pii(
        audit_db, "compliance_audit",
        ("session_id_hash", "action", "category",
         "actor_token_hash", "payload_json"),
        used_sids, ADVISOR_ID,
    ))
    findings.extend(_scan_table_for_pii(
        audit_db, "engagement_events",
        ("category", "payload_json"),
        used_sids, ADVISOR_ID,
    ))
    findings.extend(_scan_table_for_pii(
        audit_db, "feature_flag_audit",
        ("flag_name", "old_value", "new_value", "reason",
         "actor_token_hash", "source_ip"),
        used_sids, ADVISOR_ID,
    ))
    assert not findings, (
        "PII leaked into audit rows:\n" + "\n".join(findings)
    )


# --------------------------------------------------------------- pinned cases


def test_compliance_export_writes_export_requested_action(
    audit_client: TestClient, audit_db: str,
) -> None:
    """Pinned smoke case — locks ``action='export_requested'``."""
    response = drive_compliance_export(audit_client, ctx_default())
    assert response.status_code == 200, response.text
    count = row_count(
        audit_db, "compliance_audit", "action = 'export_requested'",
    )
    assert count == 1


def test_full_delete_audit_lands_before_cascade(
    audit_client: TestClient, audit_db: str,
) -> None:
    """The compliance full-delete writes audit BEFORE the cascading DELETE.

    Locks in the same audit-before-mutate pattern as the export
    download, applied to the destructive-write side. The audit row
    must persist after ``DELETE FROM sessions`` cascades.
    """
    response = drive_compliance_delete(audit_client, ctx_default())
    assert response.status_code == 200, response.text
    from app.modules.compliance._audit import hash_session_id

    sid_hash = hash_session_id(DEFAULT_SESSION_ID)
    count = row_count(
        audit_db, "compliance_audit",
        f"action = 'full_delete' AND session_id_hash = '{sid_hash}'",
    )
    assert count == 1
    assert row_count(
        audit_db, "sessions", f"id = '{DEFAULT_SESSION_ID}'",
    ) == 0
