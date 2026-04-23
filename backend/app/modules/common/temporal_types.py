"""Shared enums, Pydantic base model, and city-local time formatting.

Used across appointments, jobs, engagement, and outcomes. Depends on nothing
in feature modules (prevents circular imports). Enum values are stable
lowercase snake_case, safe to round-trip through SQLite TEXT. Timezones route
through `app.cities.config.load_city_config` — no direct YAML parsing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from zoneinfo import ZoneInfo

from pydantic import BaseModel, field_validator

from app.cities.config import load_city_config

# Enums below use stable lowercase snake_case string values (DB-safe).


class AppointmentType(str, Enum):
    COURT_HEARING = "court_hearing"
    BENEFITS_RECERT = "benefits_recert"
    CAREER_CENTER = "career_center"
    JOB_INTERVIEW = "job_interview"
    CHILDCARE_INTAKE = "childcare_intake"
    MEDICAL = "medical"
    DMV = "dmv"
    OTHER = "other"


class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    ATTENDED = "attended"
    MISSED = "missed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class JobApplicationStatus(str, Enum):
    DRAFT = "draft"
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class EngagementEventType(str, Enum):
    DIGEST_SENT = "digest_sent"
    REMINDER_SENT = "reminder_sent"
    BOUNCE = "bounce"
    SPAM_REPORT = "spam_report"
    OPEN = "open"
    APPOINTMENT_AUTO_ADVANCE = "appointment_auto_advance"
    APPOINTMENT_AUTO_MISSED_NOTICE = "appointment_auto_missed_notice"
    FEATURE_FLAG_TOGGLED = "feature_flag_toggled"
    OUTCOME_RECORDED = "outcome_recorded"


class StallLevel(str, Enum):
    NONE = "none"
    SOFT = "soft"
    MEDIUM = "medium"
    HARD = "hard"


class GenerationMethod(str, Enum):
    """How an artifact (e.g. resume section) was produced. S12b resume audit."""

    LLM = "llm"
    TEMPLATE = "template"


# city slug -> IANA timezone
TIMEZONE_BY_CITY: dict[str, str] = {
    "montgomery": "America/Chicago",
    "fort-worth": "America/Chicago",
}


class TimezoneAwareModel(BaseModel):
    """Base model for records carrying `occurred_at`; rejects naive datetimes."""

    occurred_at: datetime

    @field_validator("occurred_at")
    @classmethod
    def _require_tzinfo(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("datetime must be timezone-aware (tzinfo required)")
        return v


def _coerce_to_aware_datetime(value: str | datetime) -> datetime:
    """Accept an ISO-8601 string or datetime; return an aware UTC-anchored dt."""
    if isinstance(value, str):
        s = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
    else:
        dt = value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


_TZ_LABELS = {
    "Chicago": "CT", "New_York": "ET", "Denver": "MT", "Los_Angeles": "PT",
    "Phoenix": "MST", "Anchorage": "AKT", "Honolulu": "HT",
}


def _tz_abbrev_for(tz_name: str) -> str:
    """Best-effort short label: e.g. 'America/Chicago' -> 'CT'."""
    tail = tz_name.rsplit("/", 1)[-1]
    return _TZ_LABELS.get(tail, tail.replace("_", " "))


def format_city_local(value: str | datetime, city: str) -> str:
    """Render a UTC datetime in the given city's configured local timezone.

    City-generic port of `ops:lib/nightly_phases/timezone_utils.py:format_ct`.
    Routes validation through `app.cities.config.load_city_config`; the
    tz lookup uses the `TIMEZONE_BY_CITY` registry above.

        >>> format_city_local("2026-04-10T17:00:00Z", "montgomery")
        'Friday April 10 at 12:00pm CT'
    """
    load_city_config(city)  # validates city exists; raises otherwise.

    tz_name = TIMEZONE_BY_CITY.get(city)
    if tz_name is None:
        raise KeyError(f"No timezone configured for city {city!r}")

    dt = _coerce_to_aware_datetime(value)
    local_dt = dt.astimezone(ZoneInfo(tz_name))

    hour = local_dt.hour % 12 or 12
    ampm = "am" if local_dt.hour < 12 else "pm"
    minute = f":{local_dt.minute:02d}"
    label = _tz_abbrev_for(tz_name)
    return local_dt.strftime(f"%A %B %-d at {hour}{minute}{ampm} {label}")


__all__ = [
    "AppointmentStatus", "AppointmentType", "EngagementEventType",
    "GenerationMethod", "JobApplicationStatus", "StallLevel",
    "TIMEZONE_BY_CITY", "TimezoneAwareModel", "format_city_local",
]
