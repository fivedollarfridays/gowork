"""Dispatch helpers for appointment transactional emails (T12.10a).

Extracted from :mod:`transactional_emails` to keep the public module
under the 300-line architecture ceiling. Owns:

* profile lookup (``sessions.profile`` JSON -> email + first name),
* cooldown-gated send (T12.19 integration),
* reminder candidate scan (which SCHEDULED appointments are in window),
* the SendGrid dispatch glue that records engagement rows.

The public ``transactional_emails`` module composes these with the
rendering helpers to produce the final emails.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from app.core.config import get_settings
from app.integrations.email.sendgrid_client import send_transactional
from app.modules.appointments import persistence
from app.modules.appointments._email_rendering import (
    EmailTemplate,
    render_body,
)
from app.modules.appointments.types import Appointment
from app.modules.common.temporal_types import AppointmentStatus, format_city_local
from app.modules.engagement.cooldown import check_cooldown, record_send

# Public re-use from :mod:`transactional_emails`; kept as a forward ref to
# avoid a circular import. The dataclass lives in the public module.
_WINDOW_24H_MIN_H = 23.0
_WINDOW_24H_MAX_H = 25.0
_WINDOW_1H_MIN_H = 0.5
_WINDOW_1H_MAX_H = 1.5


def load_profile(
    db_path: str | Path, session_id: str,
) -> tuple[str | None, str]:
    """Return ``(email, first_name)`` from the sessions.profile JSON.

    Mirrors :func:`app.modules.engagement.reminder_engine._load_profile`
    — duplicated here to avoid cross-module import. Missing / malformed
    profile returns ``(None, "there")``.
    """
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT profile FROM sessions WHERE id = ?", (session_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row or not row[0]:
        return None, "there"
    try:
        profile = json.loads(row[0])
    except (json.JSONDecodeError, TypeError):
        return None, "there"
    if not isinstance(profile, dict):
        return None, "there"
    email = profile.get("email")
    first_name = profile.get("first_name") or "there"
    clean_email = (
        email.strip() if isinstance(email, str) and email.strip() else None
    )
    return clean_email, first_name


def _skip(reason: str) -> dict:
    """Build a negative-outcome dict with the given skip reason."""
    return {"success": False, "message_id": None, "skipped_reason": reason}


def compose_and_send(
    appointment: Appointment,
    *,
    template: EmailTemplate,
    db_path: str | Path,
) -> dict:
    """Render + send one appointment email. Returns the raw send outcome.

    Returns a dict with keys ``success``, ``message_id``, ``skipped_reason``
    matching :class:`EmailSendResult`. Public callers convert this into
    a :class:`TransactionalSendResult`.
    """
    if appointment.starts_at is None or appointment.id is None:
        return _skip("missing_starts_at")
    email, first_name = load_profile(db_path, appointment.session_id)
    if not email:
        return _skip("no_email")
    city = get_settings().city
    when = format_city_local(appointment.starts_at, city)
    app_host = os.environ.get("APP_HOST", "https://app.montgowork.local")
    html_body, text_body = render_body(
        appointment, first_name=first_name, template=template,
        when=when, app_host=app_host,
    )
    sg = send_transactional(
        email, template.subject, html_body, text_body,
        template.category,  # type: ignore[arg-type] — Literal narrowed by caller
        session_id=appointment.session_id, db_path=db_path,
    )
    return {
        "success": sg.success,
        "message_id": sg.message_id,
        "skipped_reason": sg.skipped_reason,
    }


def send_with_cooldown(
    appointment: Appointment,
    *,
    template: EmailTemplate,
    db_path: str | Path,
) -> dict:
    """Cooldown-gated send. Records a cooldown row on success.

    Cooldown keyed on ``(session_id, category)`` per T12.19 contract.
    Returns the same shape as :func:`compose_and_send`.
    """
    if appointment.starts_at is None or appointment.id is None:
        return _skip("missing_starts_at")
    if not check_cooldown(
        appointment.session_id, template.category, db_path=db_path,
    ):
        return _skip("cooldown")
    outcome = compose_and_send(
        appointment, template=template, db_path=db_path,
    )
    if outcome["success"]:
        record_send(
            appointment.session_id, template.category, None, db_path=db_path,
        )
    return outcome


def load_reminder_candidates(
    db_path: str | Path, now: datetime,
) -> list[tuple[Appointment, str]]:
    """Return (scheduled appointment, reminder-window label) pairs due now.

    Windows:
      * 24h -> ``[23h, 25h]`` from ``now``
      * 1h  -> ``[0.5h, 1.5h]`` from ``now``
    """
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT id FROM appointments "
            "WHERE status = 'scheduled' AND starts_at IS NOT NULL"
        ).fetchall()
    finally:
        conn.close()
    out: list[tuple[Appointment, str]] = []
    for (aid,) in rows:
        appt = persistence.select_by_id(int(aid), db_path=db_path)
        if appt is None or appt.starts_at is None:
            continue
        if appt.status != AppointmentStatus.SCHEDULED:
            continue
        delta_h = (appt.starts_at - now).total_seconds() / 3600.0
        if _WINDOW_24H_MIN_H <= delta_h <= _WINDOW_24H_MAX_H:
            out.append((appt, "24h"))
        elif _WINDOW_1H_MIN_H <= delta_h <= _WINDOW_1H_MAX_H:
            out.append((appt, "1h"))
    return out


__all__ = [
    "compose_and_send",
    "load_profile",
    "load_reminder_candidates",
    "send_with_cooldown",
]
