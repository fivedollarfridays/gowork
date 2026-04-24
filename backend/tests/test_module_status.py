"""Tests for module status contracts (T12.25b).

Each of four modules exports ``nightly_status(session_id, *, db_path) ->
ModuleStatus`` reporting health signals. ``status_collector.collect_all``
aggregates the four calls into a single list. The digest composer exposes
the aggregate on its ``DigestResult`` so advisor inbox (T12.31) can
consume it without running the collector again.

Ported from ops ``nightly_status()`` pattern (see
``ops/lib/module_status_contract.py``) — the Pydantic ``ModuleStatus``
is a city-product adaptation of the ops dict contract.

Coverage: each module under healthy + degraded conditions, ``collect_all``
aggregation ordering + independence, and the digest composer seam.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core import feature_flags
from app.core.migrations import runner
from app.modules.common.temporal_types import (
    JobApplicationStatus,
    ModuleStatus,
)
from app.modules.documents import cover_letter_builder, resume_builder
from app.modules.engagement import digest_composer, reminder_engine
from app.modules.jobs import applications
from app.modules.status_collector import collect_all

_SESSION = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
_NOW = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)
_FOR_DATE = date(2026, 4, 23)


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _reset_feature_flags() -> None:
    feature_flags._reset_state_for_tests()
    yield
    feature_flags._reset_state_for_tests()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "status.db")
    runner.apply_pending(path)
    _seed_session(path, _SESSION)
    return path


def _seed_session(path: str, sid: str) -> None:
    profile = {"email": "worker@example.com", "first_name": "Jordan"}
    conn = sqlite3.connect(path)
    try:
        conn.execute("DELETE FROM sessions WHERE id = ?", (sid,))
        conn.execute(
            "INSERT INTO sessions "
            "(id, created_at, barriers, profile, expires_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                sid,
                _NOW.isoformat(),
                json.dumps([]),
                json.dumps(profile),
                (_NOW + timedelta(days=30)).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _insert_resume(
    path: str, sid: str, *, doc_type: str, when: datetime, version: int,
) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "INSERT INTO resume_versions "
            "(session_id, doc_type, version_counter, markdown, "
            " generation_method, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (sid, doc_type, version, "body", "template", when.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def _insert_engagement_event(
    path: str, sid: str, *, category: str, when: datetime,
) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "INSERT INTO engagement_events "
            "(session_id, category, payload_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (sid, category, "{}", when.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


# -------------------- Cycle 1: ModuleStatus contract --------------------


def test_module_status_model_fields_and_health_values() -> None:
    """ModuleStatus requires module_name, health, signals, last_activity_at."""
    status = ModuleStatus(
        module_name="x", health="healthy",
        signals={"n": 3}, last_activity_at=_NOW,
    )
    assert status.module_name == "x"
    assert status.health == "healthy"
    assert status.signals == {"n": 3}
    assert status.last_activity_at == _NOW


def test_module_status_rejects_invalid_health() -> None:
    with pytest.raises(ValueError):
        ModuleStatus(
            module_name="x", health="on_fire",
            signals={}, last_activity_at=None,
        )


def test_module_status_allows_null_last_activity_for_unknown() -> None:
    status = ModuleStatus(
        module_name="x", health="unknown",
        signals={}, last_activity_at=None,
    )
    assert status.last_activity_at is None


# -------------------- Cycle 2: resume_builder nightly_status --------------------


def test_resume_builder_status_unknown_when_no_versions(db_path: str) -> None:
    status = resume_builder.nightly_status(_SESSION, db_path=db_path, now=_NOW)
    assert status.module_name == "resume_builder"
    assert status.health == "unknown"
    assert status.last_activity_at is None
    assert status.signals["resume_count"] == 0


def test_resume_builder_status_healthy_when_recent_version(db_path: str) -> None:
    _insert_resume(
        db_path, _SESSION,
        doc_type="resume", when=_NOW - timedelta(days=2), version=1,
    )
    status = resume_builder.nightly_status(_SESSION, db_path=db_path, now=_NOW)
    assert status.health == "healthy"
    assert status.signals["resume_count"] == 1
    assert status.last_activity_at is not None


def test_resume_builder_status_degraded_when_stale(db_path: str) -> None:
    _insert_resume(
        db_path, _SESSION,
        doc_type="resume", when=_NOW - timedelta(days=14), version=1,
    )
    status = resume_builder.nightly_status(_SESSION, db_path=db_path, now=_NOW)
    assert status.health == "degraded"
    assert "stale" in status.signals.get("note", "").lower()


# -------------------- Cycle 3: cover_letter_builder nightly_status --------------------


def test_cover_letter_status_unknown_when_empty(db_path: str) -> None:
    status = cover_letter_builder.nightly_status(
        _SESSION, db_path=db_path, now=_NOW,
    )
    assert status.module_name == "cover_letter_builder"
    assert status.health == "unknown"
    assert status.signals["cover_letter_count"] == 0


def test_cover_letter_status_healthy_recent(db_path: str) -> None:
    _insert_resume(
        db_path, _SESSION,
        doc_type="cover_letter", when=_NOW - timedelta(days=1), version=1,
    )
    status = cover_letter_builder.nightly_status(
        _SESSION, db_path=db_path, now=_NOW,
    )
    assert status.health == "healthy"
    assert status.signals["cover_letter_count"] == 1


def test_cover_letter_status_degraded_when_stale(db_path: str) -> None:
    _insert_resume(
        db_path, _SESSION,
        doc_type="cover_letter", when=_NOW - timedelta(days=30), version=1,
    )
    status = cover_letter_builder.nightly_status(
        _SESSION, db_path=db_path, now=_NOW,
    )
    assert status.health == "degraded"


# -------------------- Cycle 4: jobs.applications nightly_status --------------------


def test_applications_status_unknown_when_no_applications(db_path: str) -> None:
    status = applications.nightly_status(_SESSION, db_path=db_path, now=_NOW)
    assert status.module_name == "applications"
    assert status.health == "unknown"
    assert status.signals["total"] == 0


def test_applications_status_healthy_with_recent_activity(db_path: str) -> None:
    stored = applications.create(
        _SESSION,
        match_source="indeed",
        match_url="https://indeed.com/job/abc",
        company="Acme", role="Tech",
        db_path=db_path,
    )
    applications.update_status(
        stored.id, JobApplicationStatus.APPLIED,
        outcome_date=_FOR_DATE, db_path=db_path,
    )
    status = applications.nightly_status(_SESSION, db_path=db_path, now=_NOW)
    assert status.health == "healthy"
    assert status.signals["total"] >= 1
    assert status.last_activity_at is not None


def test_applications_status_degraded_when_many_pending_no_activity(
    db_path: str,
) -> None:
    # Seed 4 draft applications created 10+ days ago (stale pipeline).
    stale_ts = (_NOW - timedelta(days=12)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        for i in range(4):
            conn.execute(
                "INSERT INTO job_applications "
                "(session_id, match_source, match_url, company, role, "
                " status, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    _SESSION, "indeed",
                    f"https://indeed.com/job/{i}",
                    "Acme", "Tech", "draft", stale_ts,
                ),
            )
        conn.commit()
    finally:
        conn.close()
    status = applications.nightly_status(_SESSION, db_path=db_path, now=_NOW)
    assert status.health == "degraded"
    assert status.signals["pending"] >= 3


# -------------------- Cycle 5: reminder_engine nightly_status --------------------


def test_reminder_engine_status_unknown_when_no_events(db_path: str) -> None:
    status = reminder_engine.nightly_status(_SESSION, db_path=db_path, now=_NOW)
    assert status.module_name == "reminder_engine"
    assert status.health == "unknown"


def test_reminder_engine_status_healthy_recent_digest(db_path: str) -> None:
    _insert_engagement_event(
        db_path, _SESSION,
        category="digest_sent", when=_NOW - timedelta(hours=12),
    )
    status = reminder_engine.nightly_status(_SESSION, db_path=db_path, now=_NOW)
    assert status.health == "healthy"
    assert status.signals["digest_sent_count"] == 1


def test_reminder_engine_status_degraded_when_auto_disabled(db_path: str) -> None:
    _insert_engagement_event(
        db_path, _SESSION,
        category="reminders_auto_disabled", when=_NOW - timedelta(days=1),
    )
    status = reminder_engine.nightly_status(_SESSION, db_path=db_path, now=_NOW)
    assert status.health == "degraded"
    assert status.signals["reminders_auto_disabled"] is True


# -------------------- Cycle 6: status_collector aggregation --------------------


def test_collect_all_returns_four_module_statuses(db_path: str) -> None:
    results = collect_all(_SESSION, db_path=db_path, now=_NOW)
    assert len(results) == 4
    names = [r.module_name for r in results]
    assert set(names) == {
        "resume_builder", "cover_letter_builder",
        "applications", "reminder_engine",
    }
    for r in results:
        assert isinstance(r, ModuleStatus)


def test_collect_all_independent_of_single_module_failure(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A crashing module surfaces ``unknown`` but does not abort the collector."""
    def _boom(*_a, **_kw):
        raise RuntimeError("simulated module failure")

    monkeypatch.setattr(resume_builder, "nightly_status", _boom)
    results = collect_all(_SESSION, db_path=db_path, now=_NOW)
    assert len(results) == 4
    resume_entry = next(r for r in results if r.module_name == "resume_builder")
    assert resume_entry.health == "unknown"
    assert "error" in resume_entry.signals


# -------------------- Cycle 7: digest composer integration --------------------


def test_digest_composer_exposes_module_status(db_path: str) -> None:
    """DigestResult surfaces the aggregated status list for advisor-inbox (T12.31)."""
    result = digest_composer.compose_digest(
        _SESSION, _FOR_DATE,
        db_path=db_path, city="montgomery", now=_NOW,
    )
    assert hasattr(result, "module_status")
    assert len(result.module_status) == 4
    names = {r.module_name for r in result.module_status}
    assert names == {
        "resume_builder", "cover_letter_builder",
        "applications", "reminder_engine",
    }
