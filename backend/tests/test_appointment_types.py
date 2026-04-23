"""Tests for T12.6 — Appointment Pydantic model.

Covers:
  - Construction with all fields.
  - Pathway-auto placeholders (no starts_at, no location required).
  - User-entered appointments require location_name.
  - Timezone-aware datetime enforcement (starts_at / ends_at).
  - ends_at >= starts_at (zero-duration forbidden for scheduled appts).
  - JSON round-trip (model_dump_json -> model_validate_json).
  - barrier_link optional.
  - Enum fields re-use the shared AppointmentType / AppointmentStatus
    (no re-definition in appointments.types).
  - Past dates are allowed (historical records are legitimate inputs).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.modules.appointments.types import Appointment
from app.modules.common.temporal_types import AppointmentStatus, AppointmentType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _aware(year: int = 2026, month: int = 6, day: int = 1, hour: int = 9) -> datetime:
    """Return a fixed timezone-aware datetime (UTC)."""
    return datetime(year, month, day, hour, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Cycle 1 — basic construction
# ---------------------------------------------------------------------------


def test_appointment_with_all_fields() -> None:
    """Construct an Appointment with every field populated."""
    starts = _aware()
    ends = starts + timedelta(hours=1)
    appt = Appointment(
        id=42,
        session_id="sess-abc",
        type=AppointmentType.COURT_HEARING,
        title="Expunction hearing",
        starts_at=starts,
        ends_at=ends,
        location_name="Montgomery County Courthouse",
        location_address="101 S Lawrence St, Montgomery, AL 36104",
        barrier_link="expunction",
        status=AppointmentStatus.SCHEDULED,
        source="user",
        notes="Bring ID and paperwork",
        created_at=_aware(hour=8),
    )
    assert appt.id == 42
    assert appt.type is AppointmentType.COURT_HEARING
    assert appt.status is AppointmentStatus.SCHEDULED
    assert appt.source == "user"
    assert appt.starts_at == starts
    assert appt.ends_at == ends
    assert appt.barrier_link == "expunction"


def test_placeholder_has_no_starts_at() -> None:
    """source='pathway_auto' + starts_at=None is valid (placeholder appt)."""
    appt = Appointment(
        session_id="sess-1",
        type=AppointmentType.DMV,
        title="DMV visit (to be scheduled)",
        status=AppointmentStatus.SCHEDULED,
        source="pathway_auto",
        barrier_link="dmv",
    )
    assert appt.starts_at is None
    assert appt.ends_at is None
    assert appt.location_name is None
    assert appt.source == "pathway_auto"


def test_barrier_link_optional() -> None:
    """An appointment without a barrier_link is valid."""
    appt = Appointment(
        session_id="sess-1",
        type=AppointmentType.MEDICAL,
        title="Annual checkup",
        starts_at=_aware(),
        ends_at=_aware() + timedelta(minutes=30),
        location_name="Clinic",
        status=AppointmentStatus.SCHEDULED,
    )
    assert appt.barrier_link is None


# ---------------------------------------------------------------------------
# Cycle 2 — validators
# ---------------------------------------------------------------------------


def test_user_appointment_requires_location() -> None:
    """source='user' with a starts_at but missing location_name is rejected."""
    with pytest.raises(ValidationError):
        Appointment(
            session_id="sess-1",
            type=AppointmentType.JOB_INTERVIEW,
            title="Interview",
            starts_at=_aware(),
            ends_at=_aware() + timedelta(hours=1),
            # location_name missing
            status=AppointmentStatus.SCHEDULED,
            source="user",
        )


def test_user_appointment_rejects_whitespace_only_location() -> None:
    """Whitespace-only location_name is treated as missing."""
    with pytest.raises(ValidationError):
        Appointment(
            session_id="sess-1",
            type=AppointmentType.JOB_INTERVIEW,
            title="Interview",
            starts_at=_aware(),
            ends_at=_aware() + timedelta(hours=1),
            location_name="   ",
            status=AppointmentStatus.SCHEDULED,
            source="user",
        )


def test_starts_at_must_be_timezone_aware() -> None:
    """Naive datetime for starts_at is rejected."""
    naive = datetime(2026, 6, 1, 9, 0)  # no tzinfo
    with pytest.raises(ValidationError):
        Appointment(
            session_id="sess-1",
            type=AppointmentType.MEDICAL,
            title="Checkup",
            starts_at=naive,
            ends_at=_aware() + timedelta(hours=1),
            location_name="Clinic",
            status=AppointmentStatus.SCHEDULED,
        )


def test_ends_at_must_be_timezone_aware() -> None:
    """Naive datetime for ends_at is rejected."""
    naive_end = datetime(2026, 6, 1, 10, 0)  # no tzinfo
    with pytest.raises(ValidationError):
        Appointment(
            session_id="sess-1",
            type=AppointmentType.MEDICAL,
            title="Checkup",
            starts_at=_aware(),
            ends_at=naive_end,
            location_name="Clinic",
            status=AppointmentStatus.SCHEDULED,
        )


def test_ends_at_must_be_after_starts_at() -> None:
    """ends_at before starts_at is rejected."""
    starts = _aware()
    with pytest.raises(ValidationError):
        Appointment(
            session_id="sess-1",
            type=AppointmentType.MEDICAL,
            title="Checkup",
            starts_at=starts,
            ends_at=starts - timedelta(minutes=1),
            location_name="Clinic",
            status=AppointmentStatus.SCHEDULED,
        )


def test_zero_duration_rejected_for_user_appointments() -> None:
    """ends_at == starts_at is rejected for user appointments."""
    starts = _aware()
    with pytest.raises(ValidationError):
        Appointment(
            session_id="sess-1",
            type=AppointmentType.JOB_INTERVIEW,
            title="Interview",
            starts_at=starts,
            ends_at=starts,  # zero duration
            location_name="Office",
            status=AppointmentStatus.SCHEDULED,
            source="user",
        )


# ---------------------------------------------------------------------------
# Cycle 3 — serialization, enum sourcing, historical dates
# ---------------------------------------------------------------------------


def test_json_round_trip() -> None:
    """model_dump_json() -> model_validate_json() reproduces the same model."""
    starts = _aware()
    ends = starts + timedelta(hours=1)
    appt = Appointment(
        id=7,
        session_id="sess-xyz",
        type=AppointmentType.BENEFITS_RECERT,
        title="SNAP recert",
        starts_at=starts,
        ends_at=ends,
        location_name="DHR office",
        location_address="123 Main St",
        barrier_link=None,
        status=AppointmentStatus.SCHEDULED,
        source="user",
        notes=None,
        created_at=_aware(hour=8),
    )
    payload = appt.model_dump_json()
    restored = Appointment.model_validate_json(payload)
    assert restored == appt


def test_imports_enums_from_temporal_types() -> None:
    """type / status annotations must reference the shared enums directly."""
    type_anno = Appointment.model_fields["type"].annotation
    status_anno = Appointment.model_fields["status"].annotation
    assert type_anno is AppointmentType
    assert status_anno is AppointmentStatus


def test_past_dates_allowed() -> None:
    """A starts_at in the past is valid (historical/backfill records)."""
    past_start = datetime(2020, 1, 1, 9, 0, tzinfo=timezone.utc)
    past_end = past_start + timedelta(hours=1)
    appt = Appointment(
        session_id="sess-1",
        type=AppointmentType.COURT_HEARING,
        title="Past hearing (already occurred)",
        starts_at=past_start,
        ends_at=past_end,
        location_name="Courthouse",
        status=AppointmentStatus.ATTENDED,
        source="user",
    )
    assert appt.starts_at == past_start
    assert appt.status is AppointmentStatus.ATTENDED
