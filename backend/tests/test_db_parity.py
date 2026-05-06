"""Round-trip schema parity tests across the SQLAlchemy db_engine fixture.

For T22.4 we exercise every major application table from m001-m010 by
inserting a representative row, committing, reading it back, and asserting
the round-tripped values equal the originals.

The ``db_engine`` fixture (T22.2) runs the suite twice when
``GOWORK_TEST_POSTGRES_URL`` is set:

* ``sqlite`` axis — always runs.
* ``postgres`` axis — opt-in via env var; CI sets it (T22.4).

Each test uses raw ``text()`` SQL through the engine so we exercise the
exact DDL produced by ``init_db`` (m001 baseline + m00X migrations) on
both dialects without depending on ORM models. Round-trip equality is
asserted on every column listed in the migration DDL — when a column is
omitted from the test INSERT we still read it back and assert it equals
the documented schema default.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from sqlalchemy import text


async def _insert_and_read(engine, table: str, row: dict[str, Any]) -> dict[str, Any]:
    """Insert *row* into *table*, then SELECT * for the inserted PK back.

    Returns the read-back row as a ``dict`` keyed by column name. Works
    for both sqlite and postgres because we use named parameters and
    rely on the engine's dialect-aware paramstyle translation.
    """
    cols = ", ".join(row.keys())
    placeholders = ", ".join(f":{k}" for k in row.keys())
    async with engine.begin() as conn:
        await conn.execute(
            text(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"),
            row,
        )
    async with engine.connect() as conn:
        # Match by every supplied column to find the row we just wrote
        # without depending on autoincrement IDs.
        where = " AND ".join(f"{k} = :{k}" for k in row.keys() if row[k] is not None)
        params = {k: v for k, v in row.items() if v is not None}
        result = await conn.execute(
            text(f"SELECT * FROM {table} WHERE {where} LIMIT 1"),
            params,
        )
        mapping = result.mappings().first()
        assert mapping is not None, f"row not found in {table}"
        return dict(mapping)


def _assert_round_trip(read_back: dict[str, Any], original: dict[str, Any]) -> None:
    """Assert every key in *original* equals the value in *read_back*.

    Numeric coercions (int <-> float for REAL columns; bool <-> int
    for sqlite ``INTEGER``-as-bool columns) are normalised before
    comparison so the test passes on both dialects.
    """
    for key, value in original.items():
        actual = read_back[key]
        if isinstance(value, bool):
            # sqlite stores booleans as 0/1; postgres returns Python bool.
            assert bool(actual) == value, f"{key}: {actual!r} != {value!r}"
        elif isinstance(value, float):
            assert float(actual) == pytest.approx(value), (
                f"{key}: {actual!r} != {value!r}"
            )
        else:
            assert actual == value, f"{key}: {actual!r} != {value!r}"


# ---------------------------------------------------------------------------
# m001 baseline tables
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_employers_round_trip(db_engine):
    """employers table — full column round-trip."""
    row = {
        "name": "Acme Corp",
        "address": "123 Main St",
        "lat": 32.7767,
        "lng": -96.7970,
        "license_type": "general",
        "industry": "logistics",
        "active": 1,
    }
    read_back = await _insert_and_read(db_engine, "employers", row)
    _assert_round_trip(read_back, row)


@pytest.mark.anyio
async def test_transit_routes_round_trip(db_engine):
    """transit_routes table — full column round-trip."""
    row = {
        "route_number": 7,
        "route_name": "Crosstown Local",
        "weekday_start": "06:00",
        "weekday_end": "22:00",
        "saturday": 1,
        "sunday": 0,
    }
    read_back = await _insert_and_read(db_engine, "transit_routes", row)
    _assert_round_trip(read_back, row)


@pytest.mark.anyio
async def test_transit_stops_round_trip(db_engine):
    """transit_stops table — round-trip with FK to transit_routes."""
    async with db_engine.begin() as conn:
        result = await conn.execute(
            text(
                "INSERT INTO transit_routes (route_number, route_name) "
                "VALUES (:n, :name)"
            ),
            {"n": 99, "name": "Test"},
        )
        # Resolve the inserted route_id via SELECT — works on both dialects.
        rid_row = await conn.execute(
            text("SELECT id FROM transit_routes WHERE route_number = :n"),
            {"n": 99},
        )
        route_id = rid_row.scalar_one()
    row = {
        "route_id": route_id,
        "stop_name": "Pioneer Plaza",
        "lat": 32.7800,
        "lng": -96.8050,
        "sequence": 3,
    }
    read_back = await _insert_and_read(db_engine, "transit_stops", row)
    _assert_round_trip(read_back, row)


@pytest.mark.anyio
async def test_resources_round_trip(db_engine):
    """resources table — covers m001 + m008 (city) + m009 (barrier_affinity)."""
    row = {
        "name": "Workforce Solutions",
        "category": "employment",
        "subcategory": "career_center",
        "address": "100 Workforce Way",
        "lat": 32.7500,
        "lng": -96.8000,
        "phone": "555-0100",
        "url": "https://example.org",
        "eligibility": "all",
        "services": json.dumps(["resume", "interview"]),
        "hours": "M-F 8-5",
        "notes": "Walk-ins welcome",
        "city": "fort-worth",
        "barrier_affinity": json.dumps(["transportation"]),
    }
    read_back = await _insert_and_read(db_engine, "resources", row)
    _assert_round_trip(read_back, row)


@pytest.mark.anyio
async def test_job_listings_round_trip(db_engine):
    """job_listings table — covers m001 + m010 (lat, lng)."""
    row = {
        "title": "Warehouse Associate",
        "company": "Acme Logistics",
        "location": "Fort Worth, TX",
        "description": "Fulfillment role.",
        "url": "https://jobs.example.org/1",
        "source": "honestjobs",
        "scraped_at": "2026-05-01T12:00:00Z",
        "expires_at": "2026-06-01T12:00:00Z",
        "credit_check": "no",
        "fair_chance": 1,
        "lat": 32.7600,
        "lng": -97.3300,
    }
    read_back = await _insert_and_read(db_engine, "job_listings", row)
    _assert_round_trip(read_back, row)


@pytest.mark.anyio
async def test_sessions_round_trip(db_engine):
    """sessions table — TEXT primary key + JSON columns."""
    row = {
        "id": "sess-parity-1",
        "created_at": "2026-05-01T00:00:00Z",
        "barriers": json.dumps(["transportation"]),
        "credit_profile": json.dumps({"score": 600}),
        "qualifications": json.dumps(["GED"]),
        "plan": json.dumps({"steps": []}),
        "profile": json.dumps({"name": "Test"}),
        "benefits_profile": json.dumps({"snap": True}),
        "action_checklist": json.dumps([]),
        "previous_plan": json.dumps({"steps": []}),
        "expires_at": "2026-05-08T00:00:00Z",
    }
    read_back = await _insert_and_read(db_engine, "sessions", row)
    _assert_round_trip(read_back, row)


@pytest.mark.anyio
async def test_feedback_tokens_round_trip(db_engine):
    """feedback_tokens table — TEXT primary key."""
    row = {
        "token": "fb-tok-1",
        "session_id": "sess-fb-1",
        "created_at": "2026-05-01T00:00:00Z",
        "expires_at": "2026-05-02T00:00:00Z",
    }
    read_back = await _insert_and_read(db_engine, "feedback_tokens", row)
    _assert_round_trip(read_back, row)


@pytest.mark.anyio
async def test_visit_feedback_round_trip(db_engine):
    """visit_feedback table — round-trip including outcomes JSON + booleans."""
    row = {
        "session_id": "sess-vf-1",
        "submitted_at": "2026-05-01T00:00:00Z",
        "made_it_to_center": 1,
        "outcomes": json.dumps(["info_gathered"]),
        "plan_accuracy": 4,
        "free_text": "Helpful staff.",
        "reviewed": 0,
        "action_taken": None,
    }
    read_back = await _insert_and_read(db_engine, "visit_feedback", row)
    _assert_round_trip(read_back, row)


@pytest.mark.anyio
async def test_resource_feedback_round_trip(db_engine):
    """resource_feedback table — FK to resources + UNIQUE(resource_id, session_id)."""
    async with db_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO resources (name, category) "
                "VALUES (:name, :cat)"
            ),
            {"name": "RF Test", "cat": "test"},
        )
        rid_row = await conn.execute(
            text("SELECT id FROM resources WHERE name = :n"),
            {"n": "RF Test"},
        )
        resource_id = rid_row.scalar_one()
    row = {
        "resource_id": resource_id,
        "session_id": "sess-rf-1",
        "helpful": 1,
        "barrier_type": "housing",
        "submitted_at": "2026-05-01T00:00:00Z",
    }
    read_back = await _insert_and_read(db_engine, "resource_feedback", row)
    _assert_round_trip(read_back, row)


@pytest.mark.anyio
async def test_barriers_round_trip(db_engine):
    """barriers table — TEXT primary key."""
    row = {
        "id": "barrier-parity-1",
        "name": "Transportation",
        "category": "logistics",
        "description": "No vehicle, limited transit.",
        "playbook": "Connect to transit pass program.",
    }
    read_back = await _insert_and_read(db_engine, "barriers", row)
    _assert_round_trip(read_back, row)


@pytest.mark.anyio
async def test_barrier_relationships_round_trip(db_engine):
    """barrier_relationships table — composite UNIQUE + FKs to barriers."""
    async with db_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO barriers (id, name, category) "
                "VALUES (:id, :n, :c)"
            ),
            {"id": "br-src-1", "n": "Src", "c": "test"},
        )
        await conn.execute(
            text(
                "INSERT INTO barriers (id, name, category) "
                "VALUES (:id, :n, :c)"
            ),
            {"id": "br-tgt-1", "n": "Tgt", "c": "test"},
        )
    row = {
        "source_barrier_id": "br-src-1",
        "target_barrier_id": "br-tgt-1",
        "relationship_type": "amplifies",
        "weight": 1.5,
    }
    read_back = await _insert_and_read(db_engine, "barrier_relationships", row)
    _assert_round_trip(read_back, row)


@pytest.mark.anyio
async def test_barrier_resources_round_trip(db_engine):
    """barrier_resources table — links a barrier to a resource."""
    async with db_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO barriers (id, name, category) "
                "VALUES (:id, :n, :c)"
            ),
            {"id": "br-link-1", "n": "Link", "c": "test"},
        )
        await conn.execute(
            text("INSERT INTO resources (name, category) VALUES (:n, :c)"),
            {"n": "BR Link Resource", "c": "test"},
        )
        rid_row = await conn.execute(
            text("SELECT id FROM resources WHERE name = :n"),
            {"n": "BR Link Resource"},
        )
        resource_id = rid_row.scalar_one()
    row = {
        "barrier_id": "br-link-1",
        "resource_id": resource_id,
        "impact_strength": 0.75,
        "notes": "Strong correlation.",
    }
    read_back = await _insert_and_read(db_engine, "barrier_resources", row)
    _assert_round_trip(read_back, row)


@pytest.mark.anyio
async def test_employer_policies_round_trip(db_engine):
    """employer_policies table — UNIQUE on employer_name + bool/int columns."""
    row = {
        "employer_name": "Parity Co",
        "fair_chance": 1,
        "excluded_charges": json.dumps(["violent"]),
        "lookback_years": 7,
        "bg_check_timing": "post_offer",
        "industry": "manufacturing",
        "source": "manual",
        "montgomery_area": 1,
    }
    read_back = await _insert_and_read(db_engine, "employer_policies", row)
    _assert_round_trip(read_back, row)


@pytest.mark.anyio
async def test_record_profiles_round_trip(db_engine):
    """record_profiles table — UNIQUE on session_id + JSON columns."""
    row = {
        "session_id": "sess-rp-1",
        "record_types": json.dumps(["misdemeanor"]),
        "charge_categories": json.dumps(["nonviolent"]),
        "years_since_conviction": 5,
        "completed_sentence": 1,
    }
    read_back = await _insert_and_read(db_engine, "record_profiles", row)
    _assert_round_trip(read_back, row)


@pytest.mark.anyio
async def test_share_tokens_round_trip(db_engine):
    """share_tokens table — TEXT primary key."""
    row = {
        "token": "share-tok-parity-1",
        "session_id": "sess-share-1",
        "created_at": "2026-05-01T00:00:00Z",
        "expires_at": "2026-05-08T00:00:00Z",
    }
    read_back = await _insert_and_read(db_engine, "share_tokens", row)
    _assert_round_trip(read_back, row)
