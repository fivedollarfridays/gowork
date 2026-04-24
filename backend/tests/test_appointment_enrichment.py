"""Tests for T12.7a — Appointment enrichment + stage advance.

Covers:
- ``auto_advance_stage`` stage-map resolution across cities/barriers.
- ``merge_appointment`` field-level fill without clobbering existing values.
- ``enrichment_changed`` diff reporting.
- ``build_pipeline_summary`` aggregation per barrier/stage.
- Event-bus subscriber wiring: ``appointment.attended`` terminal advance
  emits ``barrier.cleared``; non-terminal does not; registration is
  idempotent; handler exceptions do not break emission.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core import events
from app.core.migrations import runner
from app.modules.appointments import enrichment, persistence
from app.modules.appointments.enrichment import (
    StageAdvance,
    auto_advance_stage,
    build_pipeline_summary,
    enrichment_changed,
    merge_appointment,
    register_enrichment_listener,
)
from app.modules.appointments.types import Appointment
from app.modules.common.temporal_types import (
    AppointmentStatus,
    AppointmentType,
)

_SESSION = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _isolate_event_bus() -> None:
    events.clear_all_subscribers()
    # Reset enrichment listener registration sentinel so tests can re-register.
    enrichment._REGISTRATION_SENTINEL.clear()
    yield
    events.clear_all_subscribers()
    enrichment._REGISTRATION_SENTINEL.clear()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "enrichment.db")
    runner.apply_pending(path)
    _seed_session(path, _SESSION)
    return path


def _seed_session(path: str, sid: str) -> None:
    conn = sqlite3.connect(path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (sid, now, "[]", now),
        )
        conn.commit()
    finally:
        conn.close()


def _aware(hour: int = 9) -> datetime:
    return datetime(2026, 6, 1, hour, 0, tzinfo=timezone.utc)


def _appt(
    *,
    atype: AppointmentType = AppointmentType.COURT_HEARING,
    status: AppointmentStatus = AppointmentStatus.ATTENDED,
    barrier_link: str | None = "criminal",
    stage: str = "filed",
    title: str = "Court hearing",
    location_name: str | None = "Courthouse",
    notes: str | None = None,
) -> Appointment:
    starts = _aware()
    return Appointment(
        session_id=_SESSION,
        type=atype,
        title=title,
        starts_at=starts,
        ends_at=starts + timedelta(hours=1),
        location_name=location_name,
        barrier_link=barrier_link,
        status=status,
        notes=notes or f"stage:{stage}",
    )


# -------------------- auto_advance_stage --------------------


def test_auto_advance_criminal_AL_filed_to_heard() -> None:
    """Montgomery criminal, court_hearing at 'filed' → advances to 'heard'."""
    appt = _appt(
        atype=AppointmentType.COURT_HEARING,
        barrier_link="criminal",
        notes="stage:filed",
    )
    result = auto_advance_stage(appt, city="montgomery")
    assert isinstance(result, StageAdvance)
    assert result.from_stage == "filed"
    assert result.to_stage == "heard"
    assert result.is_terminal is False


def test_auto_advance_criminal_TX_terminal_cleared() -> None:
    """Fort Worth criminal, court_hearing at 'ordered' → 'cleared' (terminal)."""
    appt = _appt(
        atype=AppointmentType.COURT_HEARING,
        barrier_link="criminal",
        notes="stage:ordered",
    )
    result = auto_advance_stage(appt, city="fort-worth")
    assert result is not None
    assert result.to_stage == "cleared"
    assert result.is_terminal is True


def test_auto_advance_benefits_enrolled_to_recerted() -> None:
    """Benefits recert appointment at 'enrolled' → 'recerted' (terminal)."""
    appt = _appt(
        atype=AppointmentType.BENEFITS_RECERT,
        barrier_link="benefits",
        notes="stage:enrolled",
    )
    result = auto_advance_stage(appt, city="montgomery")
    assert result is not None
    assert result.to_stage == "recerted"
    assert result.is_terminal is True


def test_auto_advance_returns_none_for_unrelated_type() -> None:
    """Medical appointment with no barrier mapping → no advance."""
    appt = _appt(
        atype=AppointmentType.MEDICAL,
        barrier_link=None,
        notes="stage:filed",
    )
    result = auto_advance_stage(appt, city="montgomery")
    assert result is None


def test_auto_advance_does_not_mutate_input() -> None:
    """auto_advance_stage must not mutate its appointment argument."""
    appt = _appt(notes="stage:filed")
    original_notes = appt.notes
    original_status = appt.status
    _ = auto_advance_stage(appt, city="montgomery")
    assert appt.notes == original_notes
    assert appt.status == original_status


# -------------------- merge_appointment --------------------


def test_merge_appointment_fills_missing_fields() -> None:
    """Missing location_name on existing, populated on new → merged has it."""
    existing = _appt(location_name="Temp").model_copy(
        update={"location_name": None, "notes": None}
    )
    new = _appt(location_name="Real Courthouse", notes="bring ID")
    merged = merge_appointment(existing, new)
    assert merged.location_name == "Real Courthouse"
    assert merged.notes == "bring ID"


def test_merge_appointment_preserves_existing_non_null() -> None:
    """If existing has a value, new's value must NOT overwrite it."""
    existing = _appt(location_name="First Courthouse", notes="original")
    new = _appt(location_name="Second Courthouse", notes="replacement")
    merged = merge_appointment(existing, new)
    assert merged.location_name == "First Courthouse"
    assert merged.notes == "original"


# -------------------- enrichment_changed --------------------


def test_enrichment_changed_reports_diffs() -> None:
    """Returns dict of {field: (old, new)} for each differing field."""
    existing = _appt(location_name="Old", notes="old notes")
    new = _appt(location_name="New", notes="new notes")
    diffs = enrichment_changed(existing, new)
    assert "location_name" in diffs
    assert diffs["location_name"] == ("Old", "New")
    assert "notes" in diffs
    assert diffs["notes"] == ("old notes", "new notes")


# -------------------- build_pipeline_summary --------------------


def test_build_pipeline_summary_counts_by_stage(db_path: str) -> None:
    """Seed 3 attended appts across 2 barriers → counts by (barrier,stage)."""
    # criminal/filed × 2 and benefits/enrolled × 1
    persistence.insert(
        _appt(barrier_link="criminal", notes="stage:filed"),
        db_path=db_path,
    )
    persistence.insert(
        _appt(barrier_link="criminal", notes="stage:filed"),
        db_path=db_path,
    )
    persistence.insert(
        _appt(
            atype=AppointmentType.BENEFITS_RECERT,
            barrier_link="benefits",
            notes="stage:enrolled",
        ),
        db_path=db_path,
    )
    summary = build_pipeline_summary(_SESSION, db_path=db_path)
    assert summary[("criminal", "filed")] == 2
    assert summary[("benefits", "enrolled")] == 1


# -------------------- Listener --------------------


def test_listener_emits_barrier_cleared_on_terminal_attend(
    db_path: str,
) -> None:
    """Emit appointment.attended for a terminal-stage appt → barrier.cleared."""
    register_enrichment_listener(db_path)
    captured: list[dict] = []
    events.subscribe("barrier.cleared", captured.append)

    # Fort Worth criminal at 'ordered' → 'cleared' (terminal)
    with patch(
        "app.modules.appointments.enrichment.get_settings"
    ) as mock_settings:
        mock_settings.return_value.city = "fort-worth"
        appt = _appt(
            atype=AppointmentType.COURT_HEARING,
            barrier_link="criminal",
            notes="stage:ordered",
        )
        events.emit("appointment.attended", appt.model_dump(mode="json"))

    assert captured, "barrier.cleared should have been emitted"
    payload = captured[0]
    assert payload["session_id"] == _SESSION
    assert payload["barrier_id"] == "criminal"


def test_listener_does_not_emit_on_non_terminal_attend(db_path: str) -> None:
    """Non-terminal advance must NOT emit barrier.cleared."""
    register_enrichment_listener(db_path)
    captured: list[dict] = []
    events.subscribe("barrier.cleared", captured.append)

    with patch(
        "app.modules.appointments.enrichment.get_settings"
    ) as mock_settings:
        mock_settings.return_value.city = "montgomery"
        appt = _appt(
            atype=AppointmentType.COURT_HEARING,
            barrier_link="criminal",
            notes="stage:filed",  # → heard (non-terminal)
        )
        events.emit("appointment.attended", appt.model_dump(mode="json"))

    assert captured == []


def test_listener_emits_barrier_cleared_on_job_offer(db_path: str) -> None:
    """job_application.offer always clears the 'employment' barrier."""
    register_enrichment_listener(db_path)
    captured: list[dict] = []
    events.subscribe("barrier.cleared", captured.append)

    events.emit(
        "job_application.offer",
        {"session_id": _SESSION, "id": 7, "status": "offer"},
    )

    assert captured
    assert captured[0]["session_id"] == _SESSION
    assert captured[0]["barrier_id"] == "employment"


def test_listener_idempotent_registration(db_path: str) -> None:
    """Re-registering must NOT stack handlers — single delivery per event."""
    register_enrichment_listener(db_path)
    register_enrichment_listener(db_path)
    captured: list[dict] = []
    events.subscribe("barrier.cleared", captured.append)

    with patch(
        "app.modules.appointments.enrichment.get_settings"
    ) as mock_settings:
        mock_settings.return_value.city = "fort-worth"
        appt = _appt(
            atype=AppointmentType.COURT_HEARING,
            barrier_link="criminal",
            notes="stage:ordered",
        )
        events.emit("appointment.attended", appt.model_dump(mode="json"))

    assert len(captured) == 1, (
        f"Expected exactly one barrier.cleared; got {len(captured)}"
    )


def test_handler_exception_doesnt_break_emission(db_path: str) -> None:
    """If auto_advance_stage raises, the emit call still completes cleanly."""
    register_enrichment_listener(db_path)

    with patch(
        "app.modules.appointments.enrichment.auto_advance_stage",
        side_effect=RuntimeError("boom"),
    ):
        appt = _appt(
            atype=AppointmentType.COURT_HEARING,
            barrier_link="criminal",
            notes="stage:filed",
        )
        # Must not raise — events.emit swallows handler errors.
        events.emit("appointment.attended", appt.model_dump(mode="json"))
