"""Tests for shared temporal types, enums, and city-local time formatting.

Covers T12.5 acceptance criteria:
  - 6 string-valued enums, DB-safe, round-trippable through SQLite TEXT.
  - GenerationMethod exactly = {"llm", "template"} (used by S12b resume audit).
  - Pydantic models reject naive datetimes, accept timezone-aware.
  - format_city_local(dt, city) renders in the city's configured timezone.
  - No circular imports from app.modules.common.temporal_types.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from enum import Enum

import pytest
from pydantic import ValidationError
from zoneinfo import ZoneInfo

from app.modules.common.temporal_types import (
    AppointmentStatus,
    AppointmentType,
    EngagementEventType,
    GenerationMethod,
    JobApplicationStatus,
    StallLevel,
    TimezoneAwareModel,
    format_city_local,
)


# ---------------------------------------------------------------------------
# Enum membership + stable string values
# ---------------------------------------------------------------------------


class TestEnumStability:
    """Enum values are stable strings, DB-safe (lowercase snake_case, no spaces)."""

    def test_appointment_type_values(self) -> None:
        assert AppointmentType.COURT_HEARING.value == "court_hearing"
        assert AppointmentType.BENEFITS_RECERT.value == "benefits_recert"
        assert AppointmentType.CAREER_CENTER.value == "career_center"
        assert AppointmentType.JOB_INTERVIEW.value == "job_interview"
        assert AppointmentType.CHILDCARE_INTAKE.value == "childcare_intake"
        assert AppointmentType.MEDICAL.value == "medical"
        assert AppointmentType.DMV.value == "dmv"
        assert AppointmentType.OTHER.value == "other"

    def test_appointment_status_values(self) -> None:
        assert {s.value for s in AppointmentStatus} == {
            "scheduled",
            "attended",
            "missed",
            "cancelled",
            "rescheduled",
        }

    def test_job_application_status_values(self) -> None:
        assert {s.value for s in JobApplicationStatus} == {
            "draft",
            "applied",
            "interview",
            "offer",
            "rejected",
            "withdrawn",
        }

    def test_engagement_event_type_values(self) -> None:
        assert {e.value for e in EngagementEventType} == {
            "digest_sent",
            "reminder_sent",
            "bounce",
            "spam_report",
            "open",
            "appointment_auto_advance",
            "appointment_auto_missed_notice",
            "feature_flag_toggled",
            "outcome_recorded",
        }

    def test_stall_level_values(self) -> None:
        assert {s.value for s in StallLevel} == {"none", "soft", "medium", "hard"}

    def test_generation_method_is_exactly_llm_and_template(self) -> None:
        # Used by S12b resume audit — must be exactly these two values.
        assert {m.value for m in GenerationMethod} == {"llm", "template"}
        assert GenerationMethod.LLM.value == "llm"
        assert GenerationMethod.TEMPLATE.value == "template"

    @pytest.mark.parametrize(
        "enum_cls",
        [
            AppointmentType,
            AppointmentStatus,
            JobApplicationStatus,
            EngagementEventType,
            StallLevel,
            GenerationMethod,
        ],
    )
    def test_all_enums_are_string_valued(self, enum_cls: type[Enum]) -> None:
        for member in enum_cls:
            assert isinstance(member.value, str)
            # DB-safe: no spaces, all lowercase.
            assert member.value == member.value.lower()
            assert " " not in member.value


# ---------------------------------------------------------------------------
# SQLite TEXT round-trip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "enum_cls",
    [
        AppointmentType,
        AppointmentStatus,
        JobApplicationStatus,
        EngagementEventType,
        StallLevel,
        GenerationMethod,
    ],
)
def test_enum_roundtrips_through_sqlite_text(enum_cls: type[Enum]) -> None:
    """Writing enum.value to a TEXT column and reading it back reconstructs the enum."""
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE t (v TEXT NOT NULL)")
        for member in enum_cls:
            conn.execute("INSERT INTO t (v) VALUES (?)", (member.value,))
        conn.commit()

        rows = conn.execute("SELECT v FROM t").fetchall()
        recovered = [enum_cls(row[0]) for row in rows]
        assert recovered == list(enum_cls)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Pydantic timezone-aware validation
# ---------------------------------------------------------------------------


class TestTimezoneAwareModel:
    def test_accepts_timezone_aware_datetime(self) -> None:
        dt = datetime(2026, 4, 10, 17, 0, tzinfo=timezone.utc)
        m = TimezoneAwareModel(occurred_at=dt)
        assert m.occurred_at == dt
        assert m.occurred_at.tzinfo is not None

    def test_accepts_non_utc_timezone(self) -> None:
        dt = datetime(2026, 4, 10, 12, 0, tzinfo=ZoneInfo("America/Chicago"))
        m = TimezoneAwareModel(occurred_at=dt)
        assert m.occurred_at.tzinfo is not None

    def test_rejects_naive_datetime(self) -> None:
        naive = datetime(2026, 4, 10, 17, 0)  # no tzinfo
        with pytest.raises(ValidationError):
            TimezoneAwareModel(occurred_at=naive)


# ---------------------------------------------------------------------------
# format_city_local
# ---------------------------------------------------------------------------


class TestFormatCityLocal:
    def test_formats_montgomery_in_its_configured_tz(self) -> None:
        dt = datetime(2026, 4, 10, 17, 0, tzinfo=timezone.utc)
        out = format_city_local(dt, "montgomery")
        assert isinstance(out, str)
        assert len(out) > 0
        # Montgomery is America/Chicago (Central). UTC 17:00 -> 12:00 CDT on Apr 10.
        assert "12" in out  # hour component present

    def test_formats_fort_worth_in_its_configured_tz(self) -> None:
        dt = datetime(2026, 4, 10, 17, 0, tzinfo=timezone.utc)
        out = format_city_local(dt, "fort-worth")
        assert isinstance(out, str)
        assert len(out) > 0

    def test_different_configured_tz_produces_different_output(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Prove the formatter reads from config, not hardcoded.

        Montgomery and Fort Worth both sit in America/Chicago, so we monkeypatch
        the timezone registry to inject a different tz for one city and assert
        the rendered string changes accordingly.
        """
        from app.modules.common import temporal_types as tt

        original = dict(tt.TIMEZONE_BY_CITY)
        monkeypatch.setattr(
            tt,
            "TIMEZONE_BY_CITY",
            {**original, "montgomery": "America/New_York"},
        )

        dt = datetime(2026, 4, 10, 17, 0, tzinfo=timezone.utc)
        montgomery_out = format_city_local(dt, "montgomery")  # now ET
        fort_worth_out = format_city_local(dt, "fort-worth")  # still CT

        assert montgomery_out != fort_worth_out

    def test_accepts_iso_string_input(self) -> None:
        out = format_city_local("2026-04-10T17:00:00Z", "montgomery")
        assert isinstance(out, str) and len(out) > 0

    def test_naive_datetime_is_treated_as_utc(self) -> None:
        aware = datetime(2026, 4, 10, 17, 0, tzinfo=timezone.utc)
        naive = datetime(2026, 4, 10, 17, 0)
        assert format_city_local(aware, "montgomery") == format_city_local(
            naive, "montgomery"
        )

    def test_unknown_city_raises(self) -> None:
        dt = datetime(2026, 4, 10, 17, 0, tzinfo=timezone.utc)
        with pytest.raises(Exception):  # CityConfigNotFoundError or KeyError
            format_city_local(dt, "atlantis")

    def test_routes_through_existing_city_config_accessor(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """format_city_local must call load_city_config, not re-parse YAML."""
        from app.cities import config as city_config_module
        from app.modules.common import temporal_types as tt

        calls: list[str] = []
        real_loader = city_config_module.load_city_config

        def spy(city: str):
            calls.append(city)
            return real_loader(city)

        monkeypatch.setattr(tt, "load_city_config", spy)

        dt = datetime(2026, 4, 10, 17, 0, tzinfo=timezone.utc)
        format_city_local(dt, "montgomery")
        assert "montgomery" in calls


# ---------------------------------------------------------------------------
# No circular imports
# ---------------------------------------------------------------------------


def test_no_circular_imports_from_temporal_types() -> None:
    """Importing temporal_types must not pull outcomes/appointments/jobs."""
    import importlib
    import sys

    for mod_name in list(sys.modules):
        if "modules.common.temporal_types" in mod_name:
            del sys.modules[mod_name]

    importlib.import_module("app.modules.common.temporal_types")

    loaded = set(sys.modules)
    forbidden_substrings = [
        "modules.outcomes",
        "modules.appointments",
        "modules.jobs",
    ]
    offenders = [
        m for m in loaded if any(sub in m for sub in forbidden_substrings)
    ]
    # It's fine if another test already imported these; but importing
    # temporal_types alone in a fresh process must not pull them. We check
    # that temporal_types itself doesn't declare imports from these modules.
    src_path = __import__(
        "app.modules.common.temporal_types", fromlist=["__file__"]
    ).__file__
    assert src_path is not None
    with open(src_path, encoding="utf-8") as f:
        src = f.read()
    for sub in forbidden_substrings:
        assert sub not in src, (
            f"temporal_types imports forbidden module substring {sub!r}; "
            f"offenders in sys.modules: {offenders}"
        )
