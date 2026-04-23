"""Tests for job applications lifecycle + outcomes listener (T12.11).

Covers:
- create() inserts + emits `job_application.created`, initial status DRAFT
- composite (match_source, match_url) guard: None / empty string rejected
- update_status validates transitions via ALLOWED matrix
- ALLOWED matrix parametric (every current x target pair)
- terminal states (REJECTED, WITHDRAWN) have no outgoing transitions
- list_by_session returns chronological order
- list_by_status filters correctly
- status transitions emit `job_application.<status>` events
- outcomes listener writes an append-only record per event
- outcomes record carries cleared_barriers snapshot from session profile
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.core import events
from app.core.migrations import runner
from app.modules.common.temporal_types import JobApplicationStatus
from app.modules.jobs import applications
from app.modules.jobs.job_status_transitions import (
    ALLOWED,
    InvalidJobStatusTransition,
    check_transition,
)
from app.modules.jobs.outcomes_listener import register_jobs_outcomes_listener
from app.modules.outcomes.tracker import OutcomeTracker

_SESSION = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
_SESSION_B = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _isolate_event_bus() -> None:
    events.clear_all_subscribers()
    yield
    events.clear_all_subscribers()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "jobs.db")
    runner.apply_pending(path)
    _seed_sessions(path, [_SESSION, _SESSION_B])
    return path


def _seed_sessions(
    path: str,
    ids: list[str],
    profile_by_id: dict[str, dict] | None = None,
) -> None:
    profile_by_id = profile_by_id or {}
    conn = sqlite3.connect(path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        for sid in ids:
            profile_json = json.dumps(profile_by_id.get(sid, {})) or None
            conn.execute(
                "INSERT INTO sessions (id, created_at, barriers, profile, expires_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (sid, now, "[]", profile_json, now),
            )
        conn.commit()
    finally:
        conn.close()


def _make(
    *,
    session_id: str = _SESSION,
    match_source: str = "indeed",
    match_url: str = "https://indeed.com/job/abc",
    company: str = "Acme",
    role: str = "Tech",
    resume_version_id: int | None = None,
    db_path: str,
):
    return applications.create(
        session_id,
        match_source=match_source,
        match_url=match_url,
        company=company,
        role=role,
        resume_version_id=resume_version_id,
        db_path=db_path,
    )


# -------------------- create + events --------------------


def test_create_inserts_and_emits_created_event(db_path: str) -> None:
    captured: list[dict] = []
    events.subscribe("job_application.created", captured.append)

    stored = _make(db_path=db_path)

    assert stored.id is not None
    fetched = applications.get(stored.id, db_path=db_path)
    assert fetched is not None
    assert fetched.company == "Acme"
    assert captured and captured[0]["id"] == stored.id


def test_initial_status_is_draft(db_path: str) -> None:
    stored = _make(db_path=db_path)
    assert stored.status == JobApplicationStatus.DRAFT


# -------------------- composite (source, url) guard --------------------


def test_create_rejects_none_match_source(db_path: str) -> None:
    with pytest.raises(ValueError, match="match_source"):
        applications.create(
            _SESSION,
            match_source=None,  # type: ignore[arg-type]
            match_url="https://x",
            company="Acme",
            role="Tech",
            db_path=db_path,
        )


def test_create_rejects_none_match_url(db_path: str) -> None:
    with pytest.raises(ValueError, match="match_url"):
        applications.create(
            _SESSION,
            match_source="indeed",
            match_url=None,  # type: ignore[arg-type]
            company="Acme",
            role="Tech",
            db_path=db_path,
        )


def test_create_rejects_empty_string_match_source(db_path: str) -> None:
    with pytest.raises(ValueError, match="match_source"):
        _make(match_source="", db_path=db_path)


# -------------------- transitions --------------------


def test_transition_draft_to_applied_succeeds(db_path: str) -> None:
    stored = _make(db_path=db_path)
    updated = applications.update_status(
        stored.id, JobApplicationStatus.APPLIED, db_path=db_path,
    )
    assert updated.status == JobApplicationStatus.APPLIED


def test_transition_applied_to_interview_succeeds(db_path: str) -> None:
    stored = _make(db_path=db_path)
    applications.update_status(
        stored.id, JobApplicationStatus.APPLIED, db_path=db_path,
    )
    updated = applications.update_status(
        stored.id, JobApplicationStatus.INTERVIEW, db_path=db_path,
    )
    assert updated.status == JobApplicationStatus.INTERVIEW


def test_transition_interview_to_offer_succeeds(db_path: str) -> None:
    stored = _make(db_path=db_path)
    applications.update_status(
        stored.id, JobApplicationStatus.APPLIED, db_path=db_path,
    )
    applications.update_status(
        stored.id, JobApplicationStatus.INTERVIEW, db_path=db_path,
    )
    updated = applications.update_status(
        stored.id, JobApplicationStatus.OFFER, db_path=db_path,
    )
    assert updated.status == JobApplicationStatus.OFFER


def test_terminal_rejected_has_no_outgoing_transitions() -> None:
    assert ALLOWED[JobApplicationStatus.REJECTED] == set()


def test_terminal_withdrawn_has_no_outgoing_transitions() -> None:
    assert ALLOWED[JobApplicationStatus.WITHDRAWN] == set()


_ALL_STATUSES = list(JobApplicationStatus)


@pytest.mark.parametrize("current", _ALL_STATUSES)
@pytest.mark.parametrize("target", _ALL_STATUSES)
def test_all_transitions_matrix_parametric(
    current: JobApplicationStatus, target: JobApplicationStatus,
) -> None:
    if target in ALLOWED[current]:
        check_transition(current, target)
    else:
        with pytest.raises(InvalidJobStatusTransition):
            check_transition(current, target)


# -------------------- list helpers --------------------


def test_list_by_session_chronological(db_path: str) -> None:
    first = _make(db_path=db_path, match_url="https://x/1")
    second = _make(db_path=db_path, match_url="https://x/2")

    ordered = applications.list_by_session(_SESSION, db_path=db_path)
    ids = [a.id for a in ordered]

    assert ids == [first.id, second.id]


def test_list_by_status_filters_correctly(db_path: str) -> None:
    draft = _make(db_path=db_path, match_url="https://x/1")
    other = _make(db_path=db_path, match_url="https://x/2")
    applications.update_status(
        other.id, JobApplicationStatus.APPLIED, db_path=db_path,
    )

    drafts = applications.list_by_status(
        _SESSION, JobApplicationStatus.DRAFT, db_path=db_path,
    )

    assert [a.id for a in drafts] == [draft.id]


# -------------------- event emission on transitions --------------------


def test_transition_emits_event_with_status(db_path: str) -> None:
    stored = _make(db_path=db_path)
    captured: list[dict] = []
    events.subscribe("job_application.interview", captured.append)

    applications.update_status(
        stored.id, JobApplicationStatus.APPLIED, db_path=db_path,
    )
    applications.update_status(
        stored.id, JobApplicationStatus.INTERVIEW, db_path=db_path,
    )

    assert captured and captured[0]["status"] == "interview"
    assert captured[0]["id"] == stored.id


# -------------------- outcomes listener --------------------


def test_outcomes_listener_writes_on_each_transition(db_path: str) -> None:
    register_jobs_outcomes_listener(db_path)

    stored = _make(db_path=db_path)
    applications.update_status(
        stored.id, JobApplicationStatus.APPLIED, db_path=db_path,
    )
    applications.update_status(
        stored.id, JobApplicationStatus.INTERVIEW, db_path=db_path,
    )
    applications.update_status(
        stored.id, JobApplicationStatus.OFFER, db_path=db_path,
    )

    records = OutcomeTracker(db_path).list_by_session(_SESSION)
    types = [r.signal_type for r in records]

    # create + 3 transitions = 4 records
    assert types == [
        "job_application_created",
        "job_application_applied",
        "job_application_interview",
        "job_application_offer",
    ]


def test_outcomes_listener_includes_cleared_barriers_snapshot(
    tmp_path: Path,
) -> None:
    path = str(tmp_path / "jobs_snap.db")
    runner.apply_pending(path)
    _seed_sessions(
        path,
        [_SESSION],
        profile_by_id={_SESSION: {"cleared_barriers": ["dmv"]}},
    )
    register_jobs_outcomes_listener(path)

    stored = _make(db_path=path)
    applications.update_status(
        stored.id, JobApplicationStatus.APPLIED, db_path=path,
    )

    # read raw snapshot column — the snapshot carries cleared_barriers
    conn = sqlite3.connect(path)
    try:
        rows = conn.execute(
            "SELECT event_type, barriers_cleared_snapshot_json "
            "FROM outcomes_records WHERE session_id = ? ORDER BY id",
            (_SESSION,),
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) == 2
    for _event_type, snapshot_json in rows:
        assert snapshot_json is not None
        data = json.loads(snapshot_json)
        assert data == {"cleared_barriers": ["dmv"]}
