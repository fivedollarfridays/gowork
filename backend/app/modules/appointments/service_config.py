"""Appointment ServiceConfig loader (T12.8).

Port of `ops:lib/booking_services.py` adapted to MontGoWork's per-city YAML
layout. Each city's `cities/{city}.yaml` may carry an `appointment_services`
section keyed by `AppointmentType` enum value:

    appointment_services:
      dmv:
        duration_minutes: 30
        hours_local: [["08:30", "16:00"]]
        closed_days_of_week: [5, 6]   # 0=Mon..6=Sun

Public surface:
  * ``ServiceConfig`` — frozen dataclass describing one bookable service.
  * ``ServiceConfigError`` — raised on any load/validation failure.
  * ``load_services(city)`` — returns ``dict[service_type, ServiceConfig]``.
  * ``US_FEDERAL_2026`` — hardcoded federal holiday list (initial impl;
    expand to a real calendar library if/when needed).

Holidays are attached to every ServiceConfig built by ``load_services``;
individual callers may construct ``ServiceConfig(holidays=[])`` directly
when they want a holiday-free config for tests.

Overnight windows (end <= start) are rejected at construction time — see
``test_overnight_service_rejected_by_config`` for rationale.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.cities.config import CityConfigNotFoundError, load_city_config

__all__ = [
    "US_FEDERAL_2026",
    "ServiceConfig",
    "ServiceConfigError",
    "load_services",
]


# Hardcoded US federal holidays for 2026. Extend or swap for a calendar
# library when multi-year support is needed.
US_FEDERAL_2026: list[date] = [
    date(2026, 1, 1),   # New Year's Day
    date(2026, 1, 19),  # MLK Jr Day (3rd Mon)
    date(2026, 2, 16),  # Presidents Day (3rd Mon)
    date(2026, 5, 25),  # Memorial Day (last Mon)
    date(2026, 6, 19),  # Juneteenth
    date(2026, 7, 3),   # Independence Day (observed — July 4 is Sat)
    date(2026, 9, 7),   # Labor Day
    date(2026, 10, 12), # Columbus Day
    date(2026, 11, 11), # Veterans Day
    date(2026, 11, 26), # Thanksgiving
    date(2026, 12, 25), # Christmas
]


class ServiceConfigError(ValueError):
    """Raised when appointment_services config is missing, malformed, or invalid."""


def _validate_window(
    window: Any, *, service_type: str, idx: int
) -> tuple[str, str]:
    """Validate a single [start, end] HH:MM window; reject overnight."""
    if not isinstance(window, (list, tuple)) or len(window) != 2:
        raise ServiceConfigError(
            f"service {service_type!r} window {idx}: "
            f"expected [start, end] pair, got {window!r}"
        )
    start, end = window[0], window[1]
    if not isinstance(start, str) or not isinstance(end, str):
        raise ServiceConfigError(
            f"service {service_type!r} window {idx}: "
            f"start/end must be HH:MM strings"
        )
    if start >= end:
        raise ServiceConfigError(
            f"service {service_type!r} window {idx}: "
            f"overnight/zero-length windows not supported "
            f"(got start={start!r}, end={end!r})"
        )
    return start, end


@dataclass(frozen=True)
class ServiceConfig:
    """One bookable appointment service (DMV, court hearing, etc.)."""

    service_type: str
    duration_minutes: int
    hours_local: list[tuple[str, str]]
    closed_days_of_week: set[int]
    holidays: list[date] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.duration_minutes <= 0:
            raise ServiceConfigError(
                f"service {self.service_type!r}: duration_minutes must be "
                f"positive (got {self.duration_minutes})"
            )
        if not self.hours_local:
            raise ServiceConfigError(
                f"service {self.service_type!r}: hours_local must be non-empty"
            )
        # Normalize tuples and reject overnight/reversed windows.
        normalized: list[tuple[str, str]] = []
        for idx, w in enumerate(self.hours_local):
            normalized.append(_validate_window(w, service_type=self.service_type, idx=idx))
        # Frozen dataclass: use object.__setattr__ to replace the list.
        object.__setattr__(self, "hours_local", normalized)
        object.__setattr__(self, "closed_days_of_week", set(self.closed_days_of_week))


def _parse_duration(service_type: str, raw: Any) -> int:
    try:
        return int(raw["duration_minutes"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ServiceConfigError(
            f"service {service_type!r}: duration_minutes required (int)"
        ) from exc


def _parse_hours_local(service_type: str, raw: Any) -> list[tuple[str, str]]:
    hours_raw = raw.get("hours_local")
    if not isinstance(hours_raw, list) or not hours_raw:
        raise ServiceConfigError(
            f"service {service_type!r}: hours_local must be a non-empty list"
        )
    return [tuple(w) if isinstance(w, list) else w for w in hours_raw]


def _parse_closed_days(service_type: str, raw: Any) -> set[int]:
    closed_raw = raw.get("closed_days_of_week", [])
    if not isinstance(closed_raw, list):
        raise ServiceConfigError(
            f"service {service_type!r}: closed_days_of_week must be a list"
        )
    try:
        closed = {int(d) for d in closed_raw}
    except (TypeError, ValueError) as exc:
        raise ServiceConfigError(
            f"service {service_type!r}: closed_days_of_week entries must be ints"
        ) from exc
    if any(not 0 <= d <= 6 for d in closed):
        raise ServiceConfigError(
            f"service {service_type!r}: closed_days_of_week entries must be 0..6"
        )
    return closed


def _build_service(
    service_type: str, raw: Any, *, holidays: list[date]
) -> ServiceConfig:
    """Construct a ServiceConfig from the YAML-parsed mapping for one service."""
    if not isinstance(raw, dict):
        raise ServiceConfigError(
            f"service {service_type!r}: expected mapping, got {type(raw).__name__}"
        )
    return ServiceConfig(
        service_type=service_type,
        duration_minutes=_parse_duration(service_type, raw),
        hours_local=_parse_hours_local(service_type, raw),  # type: ignore[arg-type]
        closed_days_of_week=_parse_closed_days(service_type, raw),
        holidays=list(holidays),
    )


def load_services(city: str) -> dict[str, ServiceConfig]:
    """Load ``{service_type: ServiceConfig}`` from ``cities/{city}.yaml``.

    Raises ``ServiceConfigError`` if the file is missing, unreadable, or the
    ``appointment_services`` section is absent or malformed.
    """
    try:
        load_city_config(city)  # Validates slug and existence.
    except CityConfigNotFoundError as exc:
        raise ServiceConfigError(f"city {city!r} not found") from exc

    # Re-read the YAML directly to access the appointment_services key
    # (CityConfig pydantic model ignores extras; we need the raw dict).
    import yaml

    from app.cities.config import CITIES_DIR

    path = (CITIES_DIR / f"{city}.yaml").resolve()
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except OSError as exc:  # Shouldn't happen — load_city_config verified it.
        raise ServiceConfigError(f"cannot read {path}: {exc}") from exc

    if not isinstance(data, dict) or "appointment_services" not in data:
        raise ServiceConfigError(
            f"{city!r}: 'appointment_services' section is required in {path.name}"
        )
    services_raw = data["appointment_services"]
    if not isinstance(services_raw, dict) or not services_raw:
        raise ServiceConfigError(
            f"{city!r}: 'appointment_services' must be a non-empty mapping"
        )

    return {
        key: _build_service(key, raw, holidays=US_FEDERAL_2026)
        for key, raw in services_raw.items()
    }
