"""Appointment Pydantic model (T12.6).

Shape matches the `appointments` table from migration m002:
    id, session_id, type, title, starts_at, ends_at, location_name,
    location_address, barrier_link, status, source, notes, created_at.

Enum fields re-use the shared enums from
`app.modules.common.temporal_types` — we do NOT redefine them here.

Validation rules:
  * `starts_at` / `ends_at` must be timezone-aware when provided.
  * When both are present, `ends_at` must be strictly after `starts_at`
    (zero-duration is rejected for scheduled appointments).
  * User-entered appointments (`source="user"` OR `starts_at is not None`)
    must carry a non-whitespace `location_name`.
  * Pathway-auto placeholders (`source="pathway_auto"` AND
    `starts_at is None`) skip the duration/location checks — the worker
    fills these in later.
  * Past dates are allowed — already-occurred appointments are
    legitimate inputs (e.g. marking historical records as attended).

The model round-trips through JSON so it can be used directly in API
responses and stored SQLite TEXT columns via `model_dump_json`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

from app.modules.common.temporal_types import AppointmentStatus, AppointmentType


def _require_aware(value: datetime | None) -> datetime | None:
    """Reject naive datetimes; allow None (optional placeholder)."""
    if value is None:
        return value
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError("datetime must be timezone-aware (tzinfo required)")
    return value


class Appointment(BaseModel):
    """A scheduled or historical appointment attached to a session."""

    id: int | None = None  # None until persisted; SQLite assigns.
    session_id: str
    type: AppointmentType
    title: str
    starts_at: datetime | None = None  # None for pathway-auto placeholders.
    ends_at: datetime | None = None
    location_name: str | None = None
    location_address: str | None = None
    barrier_link: str | None = None  # e.g. "dmv", "expunction".
    status: AppointmentStatus
    source: Literal["user", "pathway_auto"] = "user"
    notes: str | None = None
    created_at: datetime | None = None  # Set at persistence time.

    # Timezone-aware enforcement for all datetime fields.
    @field_validator("starts_at", "ends_at", "created_at")
    @classmethod
    def _validate_tz_aware(cls, v: datetime | None) -> datetime | None:
        return _require_aware(v)

    @model_validator(mode="after")
    def _validate_cross_fields(self) -> "Appointment":
        """Duration and location checks, relaxed for pathway-auto placeholders."""
        is_placeholder = self.source == "pathway_auto" and self.starts_at is None

        if is_placeholder:
            return self

        # Duration: when both endpoints are set, ends_at must be strictly
        # after starts_at. Zero-duration is rejected.
        if self.starts_at is not None and self.ends_at is not None:
            if self.ends_at <= self.starts_at:
                raise ValueError(
                    "ends_at must be strictly after starts_at "
                    "(zero-duration appointments are not allowed)"
                )

        # Location: once an appointment has a concrete starts_at (user
        # source, or any scheduled record), a non-whitespace location_name
        # is required.
        if self.starts_at is not None:
            name = self.location_name
            if name is None or not name.strip():
                raise ValueError(
                    "location_name is required for scheduled appointments"
                )

        return self


__all__ = ["Appointment"]
