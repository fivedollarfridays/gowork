"""CRUD tests for :mod:`app.core.queries_listings_reputation` (T24.2).

Covers the three helpers consumed by the route layer:

* ``record_event`` — validates event_kind, persists row, requires
  listing existence (404-able from route layer).
* ``get_signal_rates`` — STUB for T24.8; current contract is a
  zero-shaped dict so route + frontend can wire up before T24.8 lands.
* ``aggregate_for_employer`` — STUB for T24.8; same contract reasoning.
"""

from __future__ import annotations

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
# record_event
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_record_event_returns_int_id(session_factory):
    """Successful insert returns the new event id."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="re1")
        account_id = await make_account(session, "re1@example.com")
        new_id = await qlr.record_event(
            session,
            listing_id=listing_id,
            event_kind="response_received",
            recorded_by=account_id,
        )
    assert isinstance(new_id, int)
    assert new_id > 0


@pytest.mark.anyio
async def test_record_event_persists_full_row(session_factory):
    """Row contains listing_id, kind, session_id, notes, occurred_at."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="re2")
        account_id = await make_account(session, "re2@example.com")
        new_id = await qlr.record_event(
            session,
            listing_id=listing_id,
            event_kind="placed",
            recorded_by=account_id,
            session_id="sess-abc",
            notes="great fit",
        )
        result = await session.execute(
            text(
                "SELECT listing_id, event_kind, session_id, notes, "
                "recorded_by, occurred_at "
                "FROM listing_reputation_events WHERE id = :id"
            ),
            {"id": new_id},
        )
        row = result.first()
    assert row is not None
    mp = row._mapping
    assert mp["listing_id"] == listing_id
    assert mp["event_kind"] == "placed"
    assert mp["session_id"] == "sess-abc"
    assert mp["notes"] == "great fit"
    assert mp["recorded_by"] == account_id
    assert mp["occurred_at"] is not None


@pytest.mark.anyio
async def test_record_event_invalid_kind_raises(session_factory):
    """event_kind outside EVENT_KINDS raises ValueError."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="re3")
        account_id = await make_account(session, "re3@example.com")
        with pytest.raises(ValueError):
            await qlr.record_event(
                session,
                listing_id=listing_id,
                event_kind="not_an_event",
                recorded_by=account_id,
            )


@pytest.mark.anyio
async def test_record_event_unknown_listing_raises(session_factory):
    """Listing FK to a non-existent listing raises ValueError (404-able)."""
    async with session_factory() as session:
        account_id = await make_account(session, "re4@example.com")
        with pytest.raises(ValueError):
            await qlr.record_event(
                session,
                listing_id=99999,
                event_kind="response_received",
                recorded_by=account_id,
            )


@pytest.mark.anyio
async def test_record_event_optional_fields_default_none(session_factory):
    """session_id + notes default to None when not provided."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="re5")
        account_id = await make_account(session, "re5@example.com")
        new_id = await qlr.record_event(
            session,
            listing_id=listing_id,
            event_kind="ghosted",
            recorded_by=account_id,
        )
        result = await session.execute(
            text(
                "SELECT session_id, notes "
                "FROM listing_reputation_events WHERE id = :id"
            ),
            {"id": new_id},
        )
        row = result.first()
    assert row._mapping["session_id"] is None
    assert row._mapping["notes"] is None


@pytest.mark.anyio
async def test_record_event_accepts_all_event_kinds(session_factory):
    """Every value in EVENT_KINDS is accepted."""
    from app.core.listings_verification_schema import EVENT_KINDS

    async with session_factory() as session:
        listing_id = await make_listing(session, title="re6")
        account_id = await make_account(session, "re6@example.com")
        for kind in EVENT_KINDS:
            await qlr.record_event(
                session,
                listing_id=listing_id,
                event_kind=kind,
                recorded_by=account_id,
            )
        result = await session.execute(
            text(
                "SELECT COUNT(*) FROM listing_reputation_events "
                "WHERE listing_id = :lid"
            ),
            {"lid": listing_id},
        )
    assert int(result.scalar_one()) == len(EVENT_KINDS)


# ---------------------------------------------------------------------------
# get_signal_rates (T24.8 stub)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_signal_rates_returns_zero_shape(session_factory):
    """Stub returns a zero-shaped dict so route+frontend can wire up."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="sr1")
        rates = await qlr.get_signal_rates(session, listing_id)
    assert rates == {
        "response_rate": 0.0,
        "withdrawal_rate": 0.0,
        "placement_rate": 0.0,
        "sample_size": 0,
        "window_days": 30,
    }


@pytest.mark.anyio
async def test_get_signal_rates_window_param_echoes(session_factory):
    """Custom window_days is echoed back in the result dict."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="sr2")
        rates = await qlr.get_signal_rates(
            session, listing_id, window_days=7
        )
    assert rates["window_days"] == 7


# ---------------------------------------------------------------------------
# aggregate_for_employer (T24.8 stub)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_aggregate_for_employer_returns_zero_shape(session_factory):
    """Stub returns sample_size + window_days only."""
    async with session_factory() as session:
        result = await qlr.aggregate_for_employer(session, 42)
    assert result == {"sample_size": 0, "window_days": 30}


@pytest.mark.anyio
async def test_aggregate_for_employer_window_param_echoes(session_factory):
    """Custom window_days is echoed back."""
    async with session_factory() as session:
        result = await qlr.aggregate_for_employer(
            session, 42, window_days=14
        )
    assert result["window_days"] == 14


# Silence linter — fixtures imported for side-effect.
_unused = (verification_engine,)
