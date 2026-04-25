"""QC-coverage hub for :mod:`app.demo_seed_s12b` (S13 T13.2).

The base S12b seed plants 10 demo sessions covering appointments, jobs,
resumes, outcomes, and stall states. T13.2 layers QC-coverage state on
top so every QC suite has a demo session to exercise:

* Compliance — feedback tokens (active + expired) and baseline
  ``compliance_audit`` rows for export/delete suites.
* Weekly review — varied 7-day engagement windows so the Sunday
  composer has something to consume.
* Advisor inbox — one ``advisor_tokens`` row per city (never plaintext).
* Reminder engine — ``reminder_sent`` + ``reminders_auto_disabled``
  rows + cooldown entries to exercise opt-out / cooldown gates.

This module is the public entry point; the actual row-writing logic
lives in two spokes (compliance + engagement) so each file stays under
the 300-line / 12-function arch ceiling.

Determinism + idempotency
-------------------------
Every row id / token / hash is derived from a deterministic SHA256 over
``(session_id, slot)`` so re-running the seed on a fresh DB produces
byte-identical rows. Idempotency on a populated DB is achieved with
``INSERT OR IGNORE`` (PK collision) or per-row existence pre-checks.
Demo data carries the ``demo-`` prefix on free-form text fields so ops
can always grep it out of logs.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from app._demo_seed_compliance import (
    seed_compliance_audit,
    seed_feedback_tokens,
)
from app._demo_seed_engagement import (
    advisor_token_plaintext,
    seed_advisor_token,
    seed_engagement_window,
    seed_reminder_state,
)

__all__ = ["seed_qc_state", "advisor_token_plaintext"]


def seed_qc_state(
    conn: sqlite3.Connection,
    session_id: str,
    *,
    city: str,
    state_label: str,
    now: datetime,
) -> None:
    """Plant compliance + weekly + advisor + reminder state for one session.

    City is used to (idempotently) plant one advisor token per city the
    first time we see it; the per-city deduplication is handled inside
    :func:`seed_advisor_token`.
    """
    seed_feedback_tokens(conn, session_id, now)
    seed_compliance_audit(conn, session_id, now)
    seed_engagement_window(conn, session_id, state_label, now)
    seed_reminder_state(conn, session_id, state_label, now)
    seed_advisor_token(conn, city, now)


def seed_qc_state_default_now(
    conn: sqlite3.Connection,
    session_id: str,
    *,
    city: str,
    state_label: str,
) -> None:
    """Convenience wrapper for callers that don't pin ``now``."""
    seed_qc_state(
        conn, session_id, city=city, state_label=state_label,
        now=datetime.now(timezone.utc),
    )
