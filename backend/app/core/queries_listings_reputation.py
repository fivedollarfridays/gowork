"""Async CRUD surface for ``listing_reputation_events`` (T24.2 + T24.8).

The append-only event stream that backs the rolling-window reputation
hot path. T24.2 owned the WRITER + the read-shape contract; T24.8
fills in the rolling-window SQL behind :func:`get_signal_rates` and
:func:`aggregate_for_employer`.

Rate-computation design notes
-----------------------------
* ``response_received`` / ``withdrawn`` / ``placed`` each surface as
  their own rate (count-of-kind / sample_size).
* ``ghosted`` is the *inverse* signal of ``response_received``
  ("no response after N days") — counted in ``sample_size`` so the
  denominator captures every interaction with the listing, but
  intentionally NOT exposed as its own rate to avoid double-counting.
* Sample size is returned alongside the rates so callers can suppress
  display when n is too small (the suppression policy lives at the
  call site; this layer always returns a rate dict).
* Window cutoff uses ISO-8601 lex comparison: occurred_at is stored
  as the ISO string ``record_event`` writes, and ISO-8601 sorts
  lexicographically when the timezone offset is constant — which it
  is here (always UTC). Saves a per-row datetime parse.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.listings_verification_schema import EVENT_KINDS

#: Default rolling-window length for the signal-rate computation.
_DEFAULT_WINDOW_DAYS = 30

#: Event kinds that surface as their own rate. ``ghosted`` is excluded
#: by design — see module docstring.
_RATE_KINDS: tuple[str, ...] = ("response_received", "withdrawn", "placed")


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
    # Explicit existence probe rather than relying on the FK to fire.
    # SQLite test fixtures don't enforce foreign keys without
    # ``PRAGMA foreign_keys=ON``, so an FK-only check would silently
    # accept rows for nonexistent listings on the sqlite axis.
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


def _cutoff_iso(window_days: int) -> str:
    """ISO-8601 string for ``utcnow() - window_days`` (lex-comparable)."""
    return (
        datetime.now(timezone.utc) - timedelta(days=window_days)
    ).isoformat()


def _rates_from_counts(counts: dict[str, int], window_days: int) -> dict:
    """Build the rate-dict from an event_kind → count map.

    ``counts`` may include ``ghosted`` (counted in sample_size) plus
    any of ``_RATE_KINDS``. Missing kinds default to zero. Returns the
    canonical {response_rate, withdrawal_rate, placement_rate,
    sample_size, window_days} shape with ghosted folded into the
    denominator only.
    """
    sample_size = sum(counts.values())
    if sample_size == 0:
        return {
            "response_rate": 0.0,
            "withdrawal_rate": 0.0,
            "placement_rate": 0.0,
            "sample_size": 0,
            "window_days": window_days,
        }
    return {
        "response_rate": counts.get("response_received", 0) / sample_size,
        "withdrawal_rate": counts.get("withdrawn", 0) / sample_size,
        "placement_rate": counts.get("placed", 0) / sample_size,
        "sample_size": sample_size,
        "window_days": window_days,
    }


_LISTING_COUNTS_SQL = (
    "SELECT event_kind, COUNT(*) AS n "
    "FROM listing_reputation_events "
    "WHERE listing_id = :lid AND occurred_at >= :cutoff "
    "GROUP BY event_kind"
)


async def _fetch_kind_counts(
    session: AsyncSession, sql: str, binds: dict
) -> dict[str, int]:
    """Run a GROUP BY event_kind query, return dict of kind → count."""
    result = await session.execute(text(sql), binds)
    return {row._mapping["event_kind"]: int(row._mapping["n"]) for row in result}


async def get_signal_rates(
    session: AsyncSession,
    listing_id: int,
    window_days: int = _DEFAULT_WINDOW_DAYS,
) -> dict:
    """Rolling-window signal rates for *listing_id*.

    Single SQL query: GROUP BY event_kind on rows within
    ``utcnow() - window_days`` for this listing; aggregates in Python.
    See module docstring for the ghosted-counted-but-not-surfaced
    design choice.
    """
    counts = await _fetch_kind_counts(
        session,
        _LISTING_COUNTS_SQL,
        {"lid": listing_id, "cutoff": _cutoff_iso(window_days)},
    )
    return _rates_from_counts(counts, window_days)


_EMPLOYER_COUNTS_SQL = (
    "SELECT lre.event_kind AS event_kind, COUNT(*) AS n "
    "FROM listing_reputation_events AS lre "
    "JOIN listing_verifications AS lv "
    "  ON lv.listing_id = lre.listing_id "
    "WHERE lv.employer_account_id = :eid "
    "  AND lre.occurred_at >= :cutoff "
    "GROUP BY lre.event_kind"
)


_EMPLOYER_LISTING_COUNT_SQL = (
    "SELECT COUNT(*) FROM listing_verifications "
    "WHERE employer_account_id = :eid"
)


async def _employer_listing_count(
    session: AsyncSession, employer_account_id: int
) -> int:
    """Number of listings linked to this employer via verifications."""
    result = await session.execute(
        text(_EMPLOYER_LISTING_COUNT_SQL),
        {"eid": employer_account_id},
    )
    return int(result.scalar_one() or 0)


async def aggregate_for_employer(
    session: AsyncSession,
    employer_account_id: int,
    window_days: int = _DEFAULT_WINDOW_DAYS,
) -> dict:
    """Rolling-window rates rolled up across an employer's listings.

    Joins ``listing_reputation_events`` to ``listing_verifications`` by
    listing_id and filters by ``employer_account_id`` so the aggregate
    only sees events on listings this employer owns. Adds
    ``listing_count`` to the standard rate-dict so callers know how
    many listings contributed (e.g. to gate display when an employer
    has only one verified listing).
    """
    counts = await _fetch_kind_counts(
        session,
        _EMPLOYER_COUNTS_SQL,
        {"eid": employer_account_id, "cutoff": _cutoff_iso(window_days)},
    )
    rates = _rates_from_counts(counts, window_days)
    rates["listing_count"] = await _employer_listing_count(
        session, employer_account_id
    )
    return rates


__all__ = [
    "record_event",
    "get_signal_rates",
    "aggregate_for_employer",
]
