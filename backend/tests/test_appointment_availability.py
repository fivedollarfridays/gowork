"""Tests for T12.8 — Appointment availability engine.

Cycle plan:
  1. load_services reads appointment_services from cities/{city}.yaml.
  2. compute_available_slots basic window (empty day).
  3. Closed days / holidays -> empty list.
  4. Busy intervals subtract from availability.
  5. Unavailability blocks (recurring + one-off) subtract.
  6. DST spring-forward / fall-back correctness.
  7. compute_availability_range returns per-day dict.
  8. Fort Worth uses Central Time like Montgomery.

DST: 2026 spring-forward 2:00 -> 3:00 on Mar 8 2026 in US/Central.
     2026 fall-back 2:00 -> 1:00 on Nov 1 2026 in US/Central.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.modules.appointments.availability import (
    compute_availability_range,
    compute_available_slots,
)
from app.modules.appointments.service_config import (
    ServiceConfig,
    ServiceConfigError,
    load_services,
)
from app.modules.appointments.types import Appointment
from app.modules.common.temporal_types import AppointmentStatus, AppointmentType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


CT = ZoneInfo("America/Chicago")


def _make_service(
    *,
    service_type: str = AppointmentType.DMV.value,
    duration_minutes: int = 30,
    hours_local: list[tuple[str, str]] | None = None,
    closed_days_of_week: set[int] | None = None,
    holidays: list[date] | None = None,
) -> ServiceConfig:
    """Build a ServiceConfig for tests with sensible defaults."""
    # Use 'is None' guards — empty collections are valid explicit values.
    return ServiceConfig(
        service_type=service_type,
        duration_minutes=duration_minutes,
        hours_local=hours_local if hours_local is not None else [("09:00", "11:00")],
        closed_days_of_week=(
            closed_days_of_week if closed_days_of_week is not None else {5, 6}
        ),
        holidays=holidays if holidays is not None else [],
    )


def _appointment_at(local_dt: datetime, minutes: int = 30) -> Appointment:
    """Create a booked Appointment starting at local_dt (tz-aware)."""
    return Appointment(
        session_id="sess-test",
        type=AppointmentType.DMV,
        title="Existing",
        starts_at=local_dt,
        ends_at=local_dt + timedelta(minutes=minutes),
        location_name="Office",
        status=AppointmentStatus.SCHEDULED,
        source="user",
    )


# ---------------------------------------------------------------------------
# Cycle 1 — load_services
# ---------------------------------------------------------------------------


def test_load_services_returns_config_for_montgomery() -> None:
    """load_services('montgomery') returns dict keyed by service_type."""
    services = load_services("montgomery")
    assert "dmv" in services
    dmv = services["dmv"]
    assert isinstance(dmv, ServiceConfig)
    assert dmv.service_type == "dmv"
    assert dmv.duration_minutes > 0
    assert dmv.hours_local  # at least one window
    assert 5 in dmv.closed_days_of_week and 6 in dmv.closed_days_of_week


def test_load_services_includes_all_service_types() -> None:
    """Montgomery config has the four service types listed in the spec."""
    services = load_services("montgomery")
    assert {"court_hearing", "benefits_recert", "dmv", "childcare_intake"} <= set(
        services.keys()
    )


def test_load_services_raises_on_missing_section(tmp_path, monkeypatch) -> None:
    """load_services raises ServiceConfigError if section is missing."""
    from app.cities import config as city_config

    fake_city_dir = tmp_path
    fake_yaml = fake_city_dir / "ghostville.yaml"
    fake_yaml.write_text(
        "name: Ghostville\nstate: XX\nlocation: 'Ghostville, XX'\n"
        "zip_ranges: ['00001']\njob_adapters: []\ndata_dir: data/cities/ghostville\n"
    )
    monkeypatch.setattr(city_config, "CITIES_DIR", fake_city_dir)
    city_config.load_city_config.cache_clear()

    with pytest.raises(ServiceConfigError):
        load_services("ghostville")


def test_load_services_fort_worth_has_services() -> None:
    """Fort Worth config also has appointment_services."""
    services = load_services("fort-worth")
    assert "dmv" in services


# ---------------------------------------------------------------------------
# Cycle 2 — compute_available_slots basic windows
# ---------------------------------------------------------------------------


def test_compute_slots_empty_day_full_availability() -> None:
    """No existing appointments -> slots span the entire operating window."""
    service = _make_service(
        duration_minutes=30,
        hours_local=[("09:00", "11:00")],
        closed_days_of_week=set(),
    )
    # 2026-06-02 is a Tuesday.
    slots = compute_available_slots(
        service, [], city="montgomery", day=date(2026, 6, 2)
    )
    # 09:00, 09:30, 10:00, 10:30 -> 4 slots (ends at 11:00).
    assert len(slots) == 4
    assert all(s.tzinfo is not None for s in slots)
    assert slots[0] == datetime(2026, 6, 2, 9, 0, tzinfo=CT)
    assert slots[-1] == datetime(2026, 6, 2, 10, 30, tzinfo=CT)


def test_compute_slots_skips_closed_days() -> None:
    """Saturday is a closed day -> empty list."""
    service = _make_service()  # default closes Sat/Sun
    # 2026-06-06 is a Saturday.
    slots = compute_available_slots(
        service, [], city="montgomery", day=date(2026, 6, 6)
    )
    assert slots == []


def test_compute_slots_skips_holiday() -> None:
    """Holiday (Independence Day observed) -> empty list."""
    service = _make_service(
        holidays=[date(2026, 7, 3)],  # observed on Fri
    )
    slots = compute_available_slots(
        service, [], city="montgomery", day=date(2026, 7, 3)
    )
    assert slots == []


def test_compute_slots_multiple_windows() -> None:
    """Service with a lunch break: two windows, slots in each."""
    service = _make_service(
        duration_minutes=60,
        hours_local=[("08:00", "12:00"), ("13:00", "17:00")],
        closed_days_of_week=set(),
    )
    # Monday.
    slots = compute_available_slots(
        service, [], city="montgomery", day=date(2026, 6, 1)
    )
    # 8-12 (4 slots) + 13-17 (4 slots) = 8 slots.
    assert len(slots) == 8
    # No slot at 12:00 or 12:30 (lunch).
    assert datetime(2026, 6, 1, 12, 0, tzinfo=CT) not in slots
    assert datetime(2026, 6, 1, 13, 0, tzinfo=CT) in slots


# ---------------------------------------------------------------------------
# Cycle 3 — busy intervals subtract
# ---------------------------------------------------------------------------


def test_compute_slots_blocks_busy_interval() -> None:
    """An existing appointment at 10:00 removes the 10:00 slot."""
    service = _make_service(
        duration_minutes=30,
        hours_local=[("09:00", "11:00")],
        closed_days_of_week=set(),
    )
    booked = _appointment_at(datetime(2026, 6, 2, 10, 0, tzinfo=CT), minutes=30)
    slots = compute_available_slots(
        service, [booked], city="montgomery", day=date(2026, 6, 2)
    )
    assert datetime(2026, 6, 2, 10, 0, tzinfo=CT) not in slots
    # Other slots remain.
    assert datetime(2026, 6, 2, 9, 0, tzinfo=CT) in slots
    assert datetime(2026, 6, 2, 10, 30, tzinfo=CT) in slots


def test_compute_slots_ignores_appointments_for_other_days() -> None:
    """Appointments on other days don't subtract from this day's slots."""
    service = _make_service(
        duration_minutes=30,
        hours_local=[("09:00", "10:00")],
        closed_days_of_week=set(),
    )
    other_day = _appointment_at(
        datetime(2026, 6, 1, 9, 0, tzinfo=CT), minutes=30
    )
    slots = compute_available_slots(
        service, [other_day], city="montgomery", day=date(2026, 6, 2)
    )
    assert len(slots) == 2  # Full day available.


def test_compute_slots_skips_appointments_without_starts_at() -> None:
    """Pathway-auto placeholders without starts_at are ignored."""
    service = _make_service(
        duration_minutes=30,
        hours_local=[("09:00", "10:00")],
        closed_days_of_week=set(),
    )
    placeholder = Appointment(
        session_id="sess-1",
        type=AppointmentType.DMV,
        title="DMV (placeholder)",
        status=AppointmentStatus.SCHEDULED,
        source="pathway_auto",
    )
    slots = compute_available_slots(
        service, [placeholder], city="montgomery", day=date(2026, 6, 2)
    )
    assert len(slots) == 2


# ---------------------------------------------------------------------------
# Cycle 4 — unavailability blocks
# ---------------------------------------------------------------------------


def test_compute_slots_subtracts_recurring_unavailability_block() -> None:
    """Weekly Tue 13:00-15:00 unavailability removes those slots on Tuesdays."""
    service = _make_service(
        duration_minutes=30,
        hours_local=[("12:00", "16:00")],
        closed_days_of_week=set(),
    )
    unavail = [{"day_of_week": 1, "start_time": "13:00", "end_time": "15:00"}]
    # 2026-06-02 is Tuesday (weekday=1).
    slots = compute_available_slots(
        service,
        [],
        city="montgomery",
        day=date(2026, 6, 2),
        unavailability_blocks=unavail,
    )
    assert datetime(2026, 6, 2, 13, 0, tzinfo=CT) not in slots
    assert datetime(2026, 6, 2, 14, 30, tzinfo=CT) not in slots
    # Outside the block, slots remain.
    assert datetime(2026, 6, 2, 12, 0, tzinfo=CT) in slots
    assert datetime(2026, 6, 2, 15, 0, tzinfo=CT) in slots


def test_compute_slots_ignores_recurring_block_on_other_days() -> None:
    """Recurring Tue-only block doesn't affect Wed slots."""
    service = _make_service(
        duration_minutes=30,
        hours_local=[("13:00", "14:00")],
        closed_days_of_week=set(),
    )
    unavail = [{"day_of_week": 1, "start_time": "13:00", "end_time": "15:00"}]
    # Wednesday.
    slots = compute_available_slots(
        service,
        [],
        city="montgomery",
        day=date(2026, 6, 3),
        unavailability_blocks=unavail,
    )
    assert len(slots) == 2  # 13:00, 13:30.


def test_compute_slots_subtracts_one_off_unavailability_block() -> None:
    """One-off block with {start, end} datetimes subtracts from that day only."""
    service = _make_service(
        duration_minutes=30,
        hours_local=[("09:00", "11:00")],
        closed_days_of_week=set(),
    )
    unavail = [
        {
            "start": datetime(2026, 6, 2, 9, 30, tzinfo=CT),
            "end": datetime(2026, 6, 2, 10, 30, tzinfo=CT),
        }
    ]
    slots = compute_available_slots(
        service,
        [],
        city="montgomery",
        day=date(2026, 6, 2),
        unavailability_blocks=unavail,
    )
    assert datetime(2026, 6, 2, 9, 30, tzinfo=CT) not in slots
    assert datetime(2026, 6, 2, 10, 0, tzinfo=CT) not in slots
    assert datetime(2026, 6, 2, 9, 0, tzinfo=CT) in slots
    assert datetime(2026, 6, 2, 10, 30, tzinfo=CT) in slots


# ---------------------------------------------------------------------------
# Cycle 5 — DST
# ---------------------------------------------------------------------------


def test_compute_slots_dst_spring_forward() -> None:
    """2026-03-08 spring-forward: 2am-3am skipped.

    For a service open 01:00-04:00, a 30-min stride normally produces 6 slots,
    but with DST there is no 02:00 or 02:30 local time. Expect 4 valid slots:
    01:00, 01:30, 03:00, 03:30. Note: 2026-03-08 is a Sunday, so the service
    must explicitly allow Sundays for this test.
    """
    service = _make_service(
        duration_minutes=30,
        hours_local=[("01:00", "04:00")],
        closed_days_of_week=set(),  # Open 7 days to isolate the DST behavior.
    )
    slots = compute_available_slots(
        service, [], city="montgomery", day=date(2026, 3, 8)
    )
    # The 2am and 2:30am slots don't exist; they should be absent.
    start_hours_minutes = {(s.hour, s.minute) for s in slots}
    assert (2, 0) not in start_hours_minutes
    assert (2, 30) not in start_hours_minutes
    assert (1, 0) in start_hours_minutes
    assert (3, 0) in start_hours_minutes


def test_compute_slots_dst_fall_back_no_duplicates() -> None:
    """2026-11-01 fall-back: no duplicate UTC instants in output.

    At fall-back, 01:00-02:00 local repeats. Our stride walks forward in local
    time only — we should not emit duplicate slots. Each returned datetime is
    unique.
    """
    service = _make_service(
        duration_minutes=30,
        hours_local=[("00:30", "03:00")],
        closed_days_of_week=set(),
    )
    slots = compute_available_slots(
        service, [], city="montgomery", day=date(2026, 11, 1)
    )
    # Convert to UTC for uniqueness check (the same local time can repeat at
    # fall-back, but UTC instants are always unique).
    utc_instants = [s.astimezone(ZoneInfo("UTC")) for s in slots]
    assert len(utc_instants) == len(set(utc_instants))


# ---------------------------------------------------------------------------
# Cycle 6 — compute_availability_range and fort-worth TZ
# ---------------------------------------------------------------------------


def test_compute_availability_range_returns_all_days() -> None:
    """7-day range -> dict with 7 keys, one per day."""
    service = _make_service(
        duration_minutes=30,
        hours_local=[("09:00", "10:00")],
        closed_days_of_week=set(),
    )
    result = compute_availability_range(
        service,
        [],
        city="montgomery",
        start_day=date(2026, 6, 1),
        days_out=7,
    )
    assert len(result) == 7
    expected_days = {date(2026, 6, 1) + timedelta(days=i) for i in range(7)}
    assert set(result.keys()) == expected_days
    # Each day has 2 slots (9:00, 9:30).
    for day, slots in result.items():
        assert len(slots) == 2, f"{day} had {len(slots)} slots"


def test_compute_availability_range_reflects_closed_days() -> None:
    """Weekend days in range return empty lists when closed."""
    service = _make_service(
        duration_minutes=30,
        hours_local=[("09:00", "10:00")],
    )  # Default closes Sat/Sun.
    result = compute_availability_range(
        service,
        [],
        city="montgomery",
        start_day=date(2026, 6, 1),  # Monday.
        days_out=7,
    )
    assert result[date(2026, 6, 6)] == []  # Sat.
    assert result[date(2026, 6, 7)] == []  # Sun.
    assert result[date(2026, 6, 1)] != []  # Mon.


def test_fort_worth_config_uses_central_time() -> None:
    """Fort Worth slots come back in America/Chicago tz (same as Montgomery)."""
    service = _make_service(
        duration_minutes=30,
        hours_local=[("09:00", "10:00")],
        closed_days_of_week=set(),
    )
    slots = compute_available_slots(
        service, [], city="fort-worth", day=date(2026, 6, 2)
    )
    assert len(slots) == 2
    # ZoneInfo equality with America/Chicago (both Montgomery + Fort Worth).
    assert str(slots[0].tzinfo) == "America/Chicago"


# ---------------------------------------------------------------------------
# Cycle 7 — overnight service / validation
# ---------------------------------------------------------------------------


def test_overnight_service_rejected_by_config() -> None:
    """A window where end <= start (e.g. ['22:00', '06:00']) raises.

    Decision: we reject overnight windows at ServiceConfig construction
    time rather than splitting across midnight. Rationale: a 30-min stride
    across midnight couples two calendar dates and complicates
    busy-interval subtraction; the domain (public-agency appointments)
    does not need overnight slots.
    """
    with pytest.raises(ServiceConfigError):
        ServiceConfig(
            service_type="dmv",
            duration_minutes=30,
            hours_local=[("22:00", "06:00")],
            closed_days_of_week=set(),
            holidays=[],
        )
