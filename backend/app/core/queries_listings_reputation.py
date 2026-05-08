"""Async CRUD surface for ``listing_reputation_events`` (T24.2).

The append-only event stream that backs the rolling-window reputation
hot path. T24.2 owns the WRITER plus the read-shape contract; T24.8
will replace the stub aggregators with the real rolling-window SQL.

Why stub the rates today?
-------------------------
Routes + frontend in T24.4–T24.7 need a stable response shape to bind
to before the math lands. Returning a zero-rate dict with the final
keys lets the consumers ship without a second round of plumbing once
T24.8 fills in the computation.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.listings_verification_schema import EVENT_KINDS

#: Default rolling-window length for the signal-rate computation
#: (T24.8 will honour this; the stub just echoes it back).
_DEFAULT_WINDOW_DAYS = 30


def _utcnow_iso() -> str:
    """ISO-8601 UTC timestamp string for ``occurred_at``."""
    return datetime.now(timezone.utc).isoformat()


async def _listing_exists(session: AsyncSession, listing_id: int) -> bool:
    """Cheap existence probe so :func:`record_event` can 404 cleanly."""
    result = await session.execute(
        text("SELECT 1 FROM job_listings WHERE id = :lid"),
        {"lid": listing_id},
    )
    return result.first() is not None


_INSERT_EVENT_SQL = (
    "INSERT INTO listing_reputation_events "
    "(listing_id, event_kind, session_id, occurred_at, "
    "recorded_by, notes) "
    "VALUES (:lid, :kind, :sid, :ts, :rb, :notes) RETURNING id"
)


async def _insert_event_row(session: AsyncSession, binds: dict) -> int:
    """Insert one event row + commit; return the new id."""
    result = await session.execute(text(_INSERT_EVENT_SQL), binds)
    new_id = int(result.scalar_one())
    await session.commit()
    return new_id


async def record_event(
    session: AsyncSession,
    *,
    listing_id: int,
    event_kind: str,
    recorded_by: int | None,
    session_id: str | None = None,
    notes: str | None = None,
) -> int:
    """Insert one ``listing_reputation_events`` row, return new id.

    Validates ``event_kind`` against :data:`EVENT_KINDS` and ``listing_id``
    against the legacy ``job_listings`` table — both raise ``ValueError``
    on miss so the route layer translates to 400 / 404 cleanly without
    surfacing the dialect's CHECK / FK constraint error.
    """
    if event_kind not in EVENT_KINDS:
        raise ValueError(
            f"invalid event_kind {event_kind!r}; expected {EVENT_KINDS}"
        )
    if not await _listing_exists(session, listing_id):
        raise ValueError(f"listing {listing_id} does not exist")
    return await _insert_event_row(
        session,
        {
            "lid": listing_id,
            "kind": event_kind,
            "sid": session_id,
            "ts": _utcnow_iso(),
            "rb": recorded_by,
            "notes": notes,
        },
    )


async def get_signal_rates(
    session: AsyncSession,
    listing_id: int,
    window_days: int = _DEFAULT_WINDOW_DAYS,
) -> dict:
    """Rolling-window signal rates for *listing_id* (STUB for T24.8).

    Returns a zero-shaped dict so route + frontend can wire up the
    response surface before T24.8 lands the actual math. The keys are
    the final contract — T24.8 will only change the values.
    """
    # Touch the session so async machinery is exercised in tests
    # (and the function stays drop-in replaceable by T24.8).
    _ = session
    _ = listing_id
    return {
        "response_rate": 0.0,
        "withdrawal_rate": 0.0,
        "placement_rate": 0.0,
        "sample_size": 0,
        "window_days": window_days,
    }


async def aggregate_for_employer(
    session: AsyncSession,
    employer_account_id: int,
    window_days: int = _DEFAULT_WINDOW_DAYS,
) -> dict:
    """Rolling-window aggregation across an employer (STUB for T24.8).

    Same rationale as :func:`get_signal_rates` — the response shape is
    pinned now; T24.8 fills the values.
    """
    _ = session
    _ = employer_account_id
    return {"sample_size": 0, "window_days": window_days}


__all__ = [
    "record_event",
    "get_signal_rates",
    "aggregate_for_employer",
]
