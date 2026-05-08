"""Rolling-window signal-rate computation tests (T24.8).

Replaces the ``get_signal_rates`` + ``aggregate_for_employer`` stubs
landed in T24.2 with the actual rolling-window math:

* ``get_signal_rates`` — single-listing rates over a 30-day default
  window (configurable). Sample size returned so callers can suppress
  rates when n < 5 (the suppression itself is caller-side; this layer
  always returns rates so the contract stays ergonomic).
* ``aggregate_for_employer`` — same shape but rolled up across every
  listing owned by an employer (joined through ``listing_verifications``
  by ``employer_account_id``).

Design point exercised here: ``ghosted`` events count toward
``sample_size`` (so the denominator captures every interaction with
the listing) but are intentionally NOT surfaced as their own rate —
ghosted is the *inverse* signal of ``response_received`` and showing
both would double-count the same outcome.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core import queries_listings_reputation as qlr
from tests._listings_verification_test_fixtures import (
    make_account,
    make_listing,
    session_factory,  # noqa: F401
    verification_engine,  # noqa: F401
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _iso(dt: datetime) -> str:
    """ISO-8601 UTC string matching ``record_event``'s on-disk format."""
    return dt.astimezone(timezone.utc).isoformat()


async def _insert_event_at(
    session,
    *,
    listing_id: int,
    event_kind: str,
    occurred_at: datetime,
    recorded_by: int | None = None,
) -> None:
    """Insert one event with an explicit ``occurred_at`` timestamp.

    ``record_event`` always stamps ``utcnow()`` so it can't seed the
    "outside the window" cases. Tests bypass it for controlled fixtures.
    """
    await session.execute(
        text(
            "INSERT INTO listing_reputation_events "
            "(listing_id, event_kind, occurred_at, recorded_by) "
            "VALUES (:lid, :kind, :ts, :rb)"
        ),
        {
            "lid": listing_id,
            "kind": event_kind,
            "ts": _iso(occurred_at),
            "rb": recorded_by,
        },
    )
    await session.commit()


async def _seed_employer(session, *, name: str = "Co") -> int:
    """Insert one employer_accounts row, return its id."""
    result = await session.execute(
        text(
            "INSERT INTO employer_accounts "
            "(name, domain, verification_status, source_trust_tier, "
            "created_at) "
            "VALUES (:n, :d, 'pending', 'unknown', :ts) RETURNING id"
        ),
        {"n": name, "d": f"{name.lower()}.com", "ts": "2026-05-08T00:00:00Z"},
    )
    new_id = int(result.scalar_one())
    await session.commit()
    return new_id


async def _link_listing_to_employer(
    session, *, listing_id: int, employer_id: int
) -> None:
    """Insert one listing_verifications row tying a listing to an employer."""
    await session.execute(
        text(
            "INSERT INTO listing_verifications "
            "(listing_id, employer_account_id, verification_tier, "
            "verified_at, created_at) "
            "VALUES (:lid, :eid, 'source_trust', :ts, :ts)"
        ),
        {
            "lid": listing_id,
            "eid": employer_id,
            "ts": "2026-05-08T00:00:00Z",
        },
    )
    await session.commit()


# ---------------------------------------------------------------------------
# get_signal_rates — empty + window plumbing
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_signal_rates_empty_listing_returns_zeros(session_factory):
    """No events → all rates 0.0, sample_size 0, window echoed."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="empty")
        rates = await qlr.get_signal_rates(session, listing_id)
    assert rates == {
        "response_rate": 0.0,
        "withdrawal_rate": 0.0,
        "placement_rate": 0.0,
        "sample_size": 0,
        "window_days": 30,
    }


@pytest.mark.anyio
async def test_signal_rates_custom_window_days_echoed(session_factory):
    """Caller-supplied window_days flows through to the result dict."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="echo")
        rates = await qlr.get_signal_rates(
            session, listing_id, window_days=7
        )
    assert rates["window_days"] == 7


# ---------------------------------------------------------------------------
# get_signal_rates — rate math
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_signal_rates_mixed_events_compute_correct_rates(session_factory):
    """5 response + 2 withdrawn + 1 placed → 5/8, 2/8, 1/8, n=8."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="mix")
        now = datetime.now(timezone.utc)
        recent = now - timedelta(days=1)
        for _ in range(5):
            await _insert_event_at(
                session,
                listing_id=listing_id,
                event_kind="response_received",
                occurred_at=recent,
            )
        for _ in range(2):
            await _insert_event_at(
                session,
                listing_id=listing_id,
                event_kind="withdrawn",
                occurred_at=recent,
            )
        await _insert_event_at(
            session,
            listing_id=listing_id,
            event_kind="placed",
            occurred_at=recent,
        )
        rates = await qlr.get_signal_rates(session, listing_id)
    assert rates["sample_size"] == 8
    assert rates["response_rate"] == pytest.approx(5 / 8)
    assert rates["withdrawal_rate"] == pytest.approx(2 / 8)
    assert rates["placement_rate"] == pytest.approx(1 / 8)


@pytest.mark.anyio
async def test_signal_rates_ghosted_counts_in_sample_not_in_rates(
    session_factory,
):
    """ghosted is the inverse signal of response_received: counted in
    sample_size denominator, never surfaced as its own rate.
    """
    async with session_factory() as session:
        listing_id = await make_listing(session, title="ghost")
        now = datetime.now(timezone.utc)
        recent = now - timedelta(days=2)
        await _insert_event_at(
            session,
            listing_id=listing_id,
            event_kind="response_received",
            occurred_at=recent,
        )
        for _ in range(3):
            await _insert_event_at(
                session,
                listing_id=listing_id,
                event_kind="ghosted",
                occurred_at=recent,
            )
        rates = await qlr.get_signal_rates(session, listing_id)
    # 4 events total, 1 response_received → response_rate = 1/4
    assert rates["sample_size"] == 4
    assert rates["response_rate"] == pytest.approx(1 / 4)
    assert rates["withdrawal_rate"] == 0.0
    assert rates["placement_rate"] == 0.0
    # ghosted intentionally NOT a key on the dict
    assert "ghosted_rate" not in rates


@pytest.mark.anyio
async def test_signal_rates_small_sample_still_returns_rates(session_factory):
    """n < 5 still returns rates — suppression is caller-side, not here."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="small")
        recent = datetime.now(timezone.utc) - timedelta(hours=1)
        await _insert_event_at(
            session,
            listing_id=listing_id,
            event_kind="response_received",
            occurred_at=recent,
        )
        rates = await qlr.get_signal_rates(session, listing_id)
    assert rates["sample_size"] == 1
    assert rates["response_rate"] == pytest.approx(1.0)


@pytest.mark.anyio
async def test_signal_rates_all_event_kinds_correct(session_factory):
    """Large mixed sample exercises every event_kind branch."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="all")
        recent = datetime.now(timezone.utc) - timedelta(days=3)
        # 10 response, 5 withdrawn, 3 placed, 7 ghosted = 25 total
        kinds = (
            [("response_received", 10)]
            + [("withdrawn", 5)]
            + [("placed", 3)]
            + [("ghosted", 7)]
        )
        for kind, count in kinds:
            for _ in range(count):
                await _insert_event_at(
                    session,
                    listing_id=listing_id,
                    event_kind=kind,
                    occurred_at=recent,
                )
        rates = await qlr.get_signal_rates(session, listing_id)
    assert rates["sample_size"] == 25
    assert rates["response_rate"] == pytest.approx(10 / 25)
    assert rates["withdrawal_rate"] == pytest.approx(5 / 25)
    assert rates["placement_rate"] == pytest.approx(3 / 25)


# ---------------------------------------------------------------------------
# get_signal_rates — window cutoff
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_signal_rates_excludes_events_outside_window(session_factory):
    """Events older than window_days are excluded from sample + rates."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="window")
        now = datetime.now(timezone.utc)
        # In window: 2 response_received from last week
        for _ in range(2):
            await _insert_event_at(
                session,
                listing_id=listing_id,
                event_kind="response_received",
                occurred_at=now - timedelta(days=7),
            )
        # Outside window: 100 placed from 60 days ago — would skew
        # placement_rate to ~98% if the cutoff were ignored.
        for _ in range(100):
            await _insert_event_at(
                session,
                listing_id=listing_id,
                event_kind="placed",
                occurred_at=now - timedelta(days=60),
            )
        rates = await qlr.get_signal_rates(session, listing_id)
    assert rates["sample_size"] == 2
    assert rates["response_rate"] == pytest.approx(1.0)
    assert rates["placement_rate"] == 0.0


@pytest.mark.anyio
async def test_signal_rates_short_window_tightens_cutoff(session_factory):
    """window_days=7 excludes events from 14 days ago that 30d would keep."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="short")
        now = datetime.now(timezone.utc)
        await _insert_event_at(
            session,
            listing_id=listing_id,
            event_kind="response_received",
            occurred_at=now - timedelta(days=2),
        )
        await _insert_event_at(
            session,
            listing_id=listing_id,
            event_kind="placed",
            occurred_at=now - timedelta(days=14),
        )
        # 30-day window sees both
        wide = await qlr.get_signal_rates(session, listing_id, window_days=30)
        # 7-day window sees only the response from 2 days ago
        narrow = await qlr.get_signal_rates(
            session, listing_id, window_days=7
        )
    assert wide["sample_size"] == 2
    assert narrow["sample_size"] == 1
    assert narrow["response_rate"] == pytest.approx(1.0)
    assert narrow["placement_rate"] == 0.0


@pytest.mark.anyio
async def test_signal_rates_other_listings_excluded(session_factory):
    """Events on other listings don't leak into the requested listing."""
    async with session_factory() as session:
        target = await make_listing(session, title="target")
        other = await make_listing(session, title="other")
        recent = datetime.now(timezone.utc) - timedelta(days=1)
        await _insert_event_at(
            session,
            listing_id=other,
            event_kind="placed",
            occurred_at=recent,
        )
        rates = await qlr.get_signal_rates(session, target)
    assert rates["sample_size"] == 0


# ---------------------------------------------------------------------------
# aggregate_for_employer
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_aggregate_employer_no_listings_returns_zeros(session_factory):
    """Employer with no linked listings → zero rates, listing_count 0."""
    async with session_factory() as session:
        employer_id = await _seed_employer(session, name="EmptyCo")
        agg = await qlr.aggregate_for_employer(session, employer_id)
    assert agg == {
        "response_rate": 0.0,
        "withdrawal_rate": 0.0,
        "placement_rate": 0.0,
        "sample_size": 0,
        "window_days": 30,
        "listing_count": 0,
    }


@pytest.mark.anyio
async def test_aggregate_employer_rolls_up_across_listings(session_factory):
    """Two listings, mixed events → counts sum across both listings."""
    async with session_factory() as session:
        employer_id = await _seed_employer(session, name="MultiCo")
        l1 = await make_listing(session, title="multi1")
        l2 = await make_listing(session, title="multi2")
        await _link_listing_to_employer(
            session, listing_id=l1, employer_id=employer_id
        )
        await _link_listing_to_employer(
            session, listing_id=l2, employer_id=employer_id
        )
        recent = datetime.now(timezone.utc) - timedelta(days=2)
        # listing 1: 3 response, 1 withdrawn (n=4)
        for _ in range(3):
            await _insert_event_at(
                session,
                listing_id=l1,
                event_kind="response_received",
                occurred_at=recent,
            )
        await _insert_event_at(
            session,
            listing_id=l1,
            event_kind="withdrawn",
            occurred_at=recent,
        )
        # listing 2: 1 placed, 2 ghosted (n=3)
        await _insert_event_at(
            session,
            listing_id=l2,
            event_kind="placed",
            occurred_at=recent,
        )
        for _ in range(2):
            await _insert_event_at(
                session,
                listing_id=l2,
                event_kind="ghosted",
                occurred_at=recent,
            )
        agg = await qlr.aggregate_for_employer(session, employer_id)
    # 7 events total across the two listings
    assert agg["sample_size"] == 7
    assert agg["listing_count"] == 2
    assert agg["response_rate"] == pytest.approx(3 / 7)
    assert agg["withdrawal_rate"] == pytest.approx(1 / 7)
    assert agg["placement_rate"] == pytest.approx(1 / 7)
    assert agg["window_days"] == 30


@pytest.mark.anyio
async def test_aggregate_employer_isolates_other_employers(session_factory):
    """Events on another employer's listings don't leak in."""
    async with session_factory() as session:
        ours = await _seed_employer(session, name="OurCo")
        theirs = await _seed_employer(session, name="TheirCo")
        l_ours = await make_listing(session, title="ours")
        l_theirs = await make_listing(session, title="theirs")
        await _link_listing_to_employer(
            session, listing_id=l_ours, employer_id=ours
        )
        await _link_listing_to_employer(
            session, listing_id=l_theirs, employer_id=theirs
        )
        recent = datetime.now(timezone.utc) - timedelta(days=1)
        await _insert_event_at(
            session,
            listing_id=l_ours,
            event_kind="response_received",
            occurred_at=recent,
        )
        # 50 events on the other employer should be ignored
        for _ in range(50):
            await _insert_event_at(
                session,
                listing_id=l_theirs,
                event_kind="placed",
                occurred_at=recent,
            )
        agg = await qlr.aggregate_for_employer(session, ours)
    assert agg["sample_size"] == 1
    assert agg["listing_count"] == 1
    assert agg["response_rate"] == pytest.approx(1.0)
    assert agg["placement_rate"] == 0.0


@pytest.mark.anyio
async def test_aggregate_employer_window_cutoff(session_factory):
    """Old events outside the window are excluded from the aggregate."""
    async with session_factory() as session:
        employer_id = await _seed_employer(session, name="WindowCo")
        listing_id = await make_listing(session, title="winagg")
        await _link_listing_to_employer(
            session, listing_id=listing_id, employer_id=employer_id
        )
        now = datetime.now(timezone.utc)
        await _insert_event_at(
            session,
            listing_id=listing_id,
            event_kind="response_received",
            occurred_at=now - timedelta(days=3),
        )
        await _insert_event_at(
            session,
            listing_id=listing_id,
            event_kind="placed",
            occurred_at=now - timedelta(days=90),
        )
        agg = await qlr.aggregate_for_employer(session, employer_id)
    assert agg["sample_size"] == 1
    assert agg["response_rate"] == pytest.approx(1.0)
    assert agg["placement_rate"] == 0.0


# Silence linter — fixtures imported for side-effect.
_unused = (verification_engine,)
