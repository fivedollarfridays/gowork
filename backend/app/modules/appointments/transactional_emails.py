"""Appointment transactional email pipeline (T12.10a).

Fills the ``appointment_reminders`` scheduler job stub from S12a T12.3.
Public surface:

* :func:`send_confirmation` — invoked on ``appointment.created`` events
  via the event-bus listener. Skipped for placeholder appointments
  whose ``starts_at is None``.
* :func:`scan_and_send_reminders` — run by the scheduler every 6h. For
  each SCHEDULED appointment in the 24h (23h-25h) or 1h (0.5h-1.5h)
  window, dispatches the appropriate reminder email. Cooldown (T12.19)
  prevents duplicates on scheduler replays.
* :func:`build_manage_url` — re-exported from :mod:`_email_rendering`
  for API parity with the spec.
* :func:`register_transactional_email_listener` — idempotent subscriber
  registration for the app lifespan.

Rendering and dispatch internals live in :mod:`_email_rendering` and
:mod:`_email_dispatch` so this public module stays under the 300-line
architecture ceiling. All sends go through the SendGrid client which
already writes to ``engagement_events`` via its audit path.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.core import events
from app.modules.appointments import _email_dispatch as dispatch
from app.modules.appointments._email_rendering import (
    CATEGORY_1H,
    CATEGORY_24H,
    CATEGORY_CONFIRM,
    TEMPLATES,
    build_manage_url,
)
from app.modules.appointments.types import Appointment

logger = logging.getLogger(__name__)


# -------------------- Public dataclass --------------------


@dataclass(frozen=True)
class TransactionalSendResult:
    """Outcome of a single transactional email dispatch."""

    success: bool
    message_id: str | None
    category: str
    appointment_id: int
    # "cooldown" | "no_email" | "missing_starts_at" | "kill_switch" | None
    skipped_reason: str | None


# Listener sentinel so ``register_*_listener`` is idempotent across
# lifespan restarts. Keyed on stringified db_path.
_REGISTRATION_SENTINEL: set[str] = set()


# -------------------- Internal dispatch wrapper --------------------


def _as_result(
    outcome: dict, *, category: str, appointment_id: int,
) -> TransactionalSendResult:
    """Convert a dispatch outcome dict into the public result dataclass."""
    return TransactionalSendResult(
        success=bool(outcome.get("success")),
        message_id=outcome.get("message_id"),
        category=category,
        appointment_id=appointment_id,
        skipped_reason=outcome.get("skipped_reason"),
    )


# Re-exported so tests can monkey-patch ``tokens_sign`` on this module
# if they want to spy the signer (kept as a lookup slot).
from app.modules.appointments.tokens import sign as tokens_sign  # noqa: E402,F401


# -------------------- Public sends --------------------


def send_confirmation(
    appointment: Appointment, *, db_path: str | Path,
) -> TransactionalSendResult:
    """Send the booking confirmation email.

    Skipped cleanly (``skipped_reason="missing_starts_at"``) for
    placeholder appointments. Cooldown-gated so a duplicate
    ``appointment.created`` emission does not double-send.
    """
    outcome = dispatch.send_with_cooldown(
        appointment, template=TEMPLATES[CATEGORY_CONFIRM], db_path=db_path,
    )
    return _as_result(
        outcome, category=CATEGORY_CONFIRM,
        appointment_id=int(appointment.id or 0),
    )


def scan_and_send_reminders(
    *,
    db_path: str | Path,
    now: datetime | None = None,
) -> list[TransactionalSendResult]:
    """Scan SCHEDULED appointments; dispatch 24h + 1h reminders.

    Entry point for the ``appointment_reminders`` scheduler job (every
    6h). Cooldown prevents duplicate sends on replays; appointments
    outside both windows are ignored.
    """
    resolved_now = now or datetime.now(timezone.utc)
    candidates = dispatch.load_reminder_candidates(db_path, resolved_now)
    results: list[TransactionalSendResult] = []
    for appt, window in candidates:
        category = CATEGORY_24H if window == "24h" else CATEGORY_1H
        outcome = dispatch.send_with_cooldown(
            appt, template=TEMPLATES[category], db_path=db_path,
        )
        results.append(
            _as_result(
                outcome, category=category,
                appointment_id=int(appt.id or 0),
            ),
        )
    return results


# -------------------- Event-bus listener --------------------


def register_transactional_email_listener(db_path: str | Path) -> None:
    """Subscribe :func:`send_confirmation` to ``appointment.created``.

    Idempotent via :data:`_REGISTRATION_SENTINEL` keyed on ``db_path``
    so repeat calls (lifespan restarts, test reuse) never stack
    duplicate handlers on the event bus.
    """
    key = str(db_path)
    if key in _REGISTRATION_SENTINEL:
        return

    def _handler(payload: dict) -> None:
        try:
            appt = Appointment.model_validate(payload)
        except Exception:  # noqa: BLE001 — isolate bad payloads
            logger.exception(
                "transactional_email listener: invalid appointment payload",
            )
            return
        send_confirmation(appt, db_path=db_path)

    events.subscribe("appointment.created", _handler)
    _REGISTRATION_SENTINEL.add(key)


__all__ = [
    "TransactionalSendResult",
    "build_manage_url",
    "register_transactional_email_listener",
    "scan_and_send_reminders",
    "send_confirmation",
]
