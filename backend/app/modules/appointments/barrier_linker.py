"""Pathway barrier -> appointment placeholder auto-linker (T12.9).

Given a `PathwayResult` produced by `app.modules.pathway.engine`, create
idempotent placeholder `Appointment` rows for barriers that require a
scheduled real-world event (court hearings, benefits recerts, DMV
visits, childcare intake). Placeholders carry `source="pathway_auto"`
and `starts_at=None` until the worker fills them in.

This module is session-aware and persistence-aware; it is invoked from
the route layer (`routes/pathway.py`, `routes/plan_intelligence.py`)
AFTER `generate_pathways()` returns. The pathway engine itself stays
pure — it does not import this module.

Public surface:
    auto_generate_placeholders(session_id, pathway_result, *, city, db_path)
    find_placeholder_matches(new_appointment, *, db_path)
    validate_patch(existing, patch)
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from app.modules.appointments import scheduler
from app.modules.appointments.types import Appointment
from app.modules.common.temporal_types import (
    AppointmentStatus,
    AppointmentType,
)
from app.modules.pathway.types import PathwayResult


# -------------------- Agency / title templates --------------------


# City slug -> agency role -> agency name. City slugs use hyphens
# (match `_CITY_SLUG_RE` from `app.core.config`).
_AGENCY_BY_CITY: dict[str, dict[str, str]] = {
    "montgomery": {
        "benefits": "DHR",     # Alabama Department of Human Resources
        "dmv": "ALEA",         # Alabama Law Enforcement Agency DMV
        "court": "Alabama circuit court",
    },
    "fort-worth": {
        "benefits": "HHSC",    # Texas Health and Human Services
        "dmv": "DPS",          # Texas Department of Public Safety
        "court": "Texas district court",
    },
}

_DEFAULT_AGENCY: dict[str, str] = {
    "benefits": "benefits office",
    "dmv": "state DMV",
    "court": "court",
}


def _agency(city: str, role: str) -> str:
    return _AGENCY_BY_CITY.get(city, _DEFAULT_AGENCY).get(
        role, _DEFAULT_AGENCY[role],
    )


def _title_for(barrier: str, city: str) -> str:
    court = _agency(city, "court")
    benefits = _agency(city, "benefits")
    if barrier == "expunction":
        return f"Court hearing — expungement filing ({court})"
    if barrier == "nondisclosure":
        return f"Court hearing — nondisclosure petition ({court})"
    if barrier == "benefits_recert":
        return f"{benefits} recertification appointment"
    if barrier == "dmv_license":
        return "DMV — license restoration"
    if barrier == "childcare_intake":
        return "Childcare provider intake"
    return ""  # defensive; _BARRIER_TO_TYPE gates entry.


# Barrier id -> appointment type. Barriers not present here generate
# no placeholder (e.g. credit_dispute has no scheduled event).
_BARRIER_TO_TYPE: dict[str, AppointmentType] = {
    "expunction": AppointmentType.COURT_HEARING,
    "nondisclosure": AppointmentType.COURT_HEARING,
    "benefits_recert": AppointmentType.BENEFITS_RECERT,
    "dmv_license": AppointmentType.DMV,
    "childcare_intake": AppointmentType.CHILDCARE_INTAKE,
}


# -------------------- Placeholder generation --------------------


def auto_generate_placeholders(
    session_id: str,
    pathway_result: PathwayResult,
    *,
    city: str,
    db_path: str | Path,
) -> list[Appointment]:
    """Create placeholder appointments for barriers needing scheduled events.

    Idempotent: a second call with the same inputs returns []; no
    duplicate rows are inserted. Placeholders have `starts_at=None`,
    `source="pathway_auto"`, and `barrier_link` set to the barrier id.
    """
    barrier_ids = _collect_barrier_ids(pathway_result)
    existing = _existing_placeholder_keys(session_id, db_path)
    created: list[Appointment] = []
    for barrier in barrier_ids:
        appt_type = _BARRIER_TO_TYPE.get(barrier)
        if appt_type is None:
            continue
        key = (appt_type, barrier)
        if key in existing:
            continue
        placeholder = _build_placeholder(session_id, barrier, appt_type, city)
        stored = scheduler.create(session_id, placeholder, db_path=db_path)
        created.append(stored)
        existing.add(key)
    return created


def _collect_barrier_ids(pathway_result: PathwayResult) -> list[str]:
    """Pull unique barrier ids from the pathway result, preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for barrier in pathway_result.barriers_active:
        if barrier not in seen:
            seen.add(barrier)
            out.append(barrier)
    return out


def _existing_placeholder_keys(
    session_id: str, db_path: str | Path,
) -> set[tuple[AppointmentType, str]]:
    """(type, barrier_link) for pathway_auto placeholders already present."""
    keys: set[tuple[AppointmentType, str]] = set()
    for appt in scheduler.list_by_session(session_id, db_path=db_path):
        if appt.source != "pathway_auto":
            continue
        if appt.barrier_link is None:
            continue
        keys.add((appt.type, appt.barrier_link))
    return keys


def _build_placeholder(
    session_id: str,
    barrier: str,
    appt_type: AppointmentType,
    city: str,
) -> Appointment:
    return Appointment(
        session_id=session_id,
        type=appt_type,
        title=_title_for(barrier, city),
        starts_at=None,
        source="pathway_auto",
        barrier_link=barrier,
        status=AppointmentStatus.SCHEDULED,
    )


# -------------------- Reconciliation --------------------


def find_placeholder_matches(
    new_appointment: Appointment, *, db_path: str | Path,
) -> list[Appointment]:
    """Return unfilled placeholders that this new appointment could fill.

    Match rules (all must hold):
      * same session_id
      * same appointment type
      * same barrier_link (only applied when the new appointment has one)
      * source == "pathway_auto"
      * starts_at is None (placeholder still unfilled)
    """
    matches: list[Appointment] = []
    for appt in scheduler.list_by_session(
        new_appointment.session_id, db_path=db_path,
    ):
        if not _is_unfilled_placeholder(appt):
            continue
        if appt.type != new_appointment.type:
            continue
        if new_appointment.barrier_link is not None:
            if appt.barrier_link != new_appointment.barrier_link:
                continue
        matches.append(appt)
    return matches


def _is_unfilled_placeholder(appt: Appointment) -> bool:
    return appt.source == "pathway_auto" and appt.starts_at is None


# -------------------- Patch validation --------------------


_IMMUTABLE_PATCH_FIELDS: tuple[str, ...] = (
    "session_id", "type", "barrier_link",
)


def validate_patch(existing: Appointment, patch: dict) -> None:
    """Reject patches that mutate identity-defining fields.

    Raises `ValueError` if the patch attempts to change `session_id`,
    `type`, or `barrier_link`. Other fields (notably `starts_at`,
    `ends_at`, `location_name`, `notes`) are allowed so a worker can
    fill a placeholder with concrete scheduling details.
    """
    for field in _IMMUTABLE_PATCH_FIELDS:
        if field not in patch:
            continue
        new_value = patch[field]
        current = getattr(existing, field)
        if new_value != current:
            raise ValueError(
                f"patch may not change {field} "
                f"(existing={current!r}, patch={new_value!r})"
            )


__all__: Iterable[str] = (
    "auto_generate_placeholders",
    "find_placeholder_matches",
    "validate_patch",
)
