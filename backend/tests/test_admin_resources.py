"""Tests for admin resource CRUD endpoints (T26.2).

Covers the six routes mounted under ``/api/admin/resources/...``, all
gated by :func:`require_role("admin")`:

* ``GET    /api/admin/resources?city=&limit=&offset=&include_hidden=``
* ``GET    /api/admin/resources/{id}``
* ``POST   /api/admin/resources``
* ``PATCH  /api/admin/resources/{id}``
* ``DELETE /api/admin/resources/{id}``  (soft-hide via set_health_status)
* ``POST   /api/admin/resources/{id}/restore``  (sets health_status='healthy')

Tests mount the router on a fresh FastAPI app to stay independent of the
router-registration edit in ``routes/__init__.py`` (also owned by T26.2).
The DB layer is the real one — the ``test_engine`` fixture swaps the
global engine to a fresh sqlite file, so query helpers run end-to-end
against the m001 + 0015 schema.

The seed loader-respect contract (T26.1) is exercised in the companion
file ``test_admin_resources_seed_respect.py``.
"""

from __future__ import annotations

import pytest

from tests._admin_resources_helpers import (
    read_resource_row,
    seed_admin,
    seed_non_admin,
    seed_resource,
)
from app.routes._auth_claim_helpers import SESSION_COOKIE_NAME


# Register the helpers module as a pytest plugin so its fixtures
# (resources_engine, session_factory, admin_resources_client) are
# discovered by name without colliding with the function-arg
# rebindings ruff flags as F811.
pytest_plugins = ["tests._admin_resources_helpers"]


# =====================================================================
# Cycle 1: auth gating — anonymous + non-admin must hit 403 on every route
# =====================================================================


@pytest.mark.anyio
async def test_list_anonymous_returns_403(admin_resources_client):
    resp = await admin_resources_client.get("/api/admin/resources")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_list_non_admin_returns_403(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        _id, cookie = await seed_non_admin(session, "u-list@example.com")
    resp = await admin_resources_client.get(
        "/api/admin/resources",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_get_anonymous_returns_403(admin_resources_client):
    resp = await admin_resources_client.get("/api/admin/resources/1")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_create_anonymous_returns_403(admin_resources_client):
    resp = await admin_resources_client.post(
        "/api/admin/resources",
        json={"name": "x", "category": "social_service", "city": "fort-worth"},
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_patch_anonymous_returns_403(admin_resources_client):
    resp = await admin_resources_client.patch(
        "/api/admin/resources/1", json={"name": "y"},
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_delete_anonymous_returns_403(admin_resources_client):
    resp = await admin_resources_client.delete("/api/admin/resources/1")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_restore_anonymous_returns_403(admin_resources_client):
    resp = await admin_resources_client.post(
        "/api/admin/resources/1/restore"
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_create_non_admin_returns_403(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        _id, cookie = await seed_non_admin(session, "u-create@example.com")
    resp = await admin_resources_client.post(
        "/api/admin/resources",
        json={"name": "x", "category": "social_service", "city": "fort-worth"},
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 403


# =====================================================================
# Cycle 2: list_resources — pagination, city filter, include_hidden
# =====================================================================


@pytest.mark.anyio
async def test_list_admin_returns_paginated_envelope(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        # Use a unique city slug to isolate from the production seed.
        for i in range(3):
            await seed_resource(
                session, name=f"R{i}", city="t26-2-listing",
            )
        _aid, cookie = await seed_admin(session, "admin-list@example.com")

    resp = await admin_resources_client.get(
        "/api/admin/resources?city=t26-2-listing",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert body["total"] == 3
    assert len(body["items"]) == 3
    # Each item should at least carry id, name, category, city, health_status.
    item = body["items"][0]
    for key in ("id", "name", "category", "city", "health_status"):
        assert key in item


@pytest.mark.anyio
async def test_list_excludes_hidden_by_default(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        await seed_resource(
            session, name="visible-1", city="t26-2-hidden",
            health_status="healthy",
        )
        await seed_resource(
            session, name="hidden-1", city="t26-2-hidden",
            health_status="hidden",
        )
        _aid, cookie = await seed_admin(session, "admin-hide@example.com")

    resp = await admin_resources_client.get(
        "/api/admin/resources?city=t26-2-hidden",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    body = resp.json()
    assert body["total"] == 1
    assert {item["name"] for item in body["items"]} == {"visible-1"}


@pytest.mark.anyio
async def test_list_include_hidden_returns_hidden_rows(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        await seed_resource(
            session, name="visible-2", city="t26-2-incl",
            health_status="healthy",
        )
        await seed_resource(
            session, name="hidden-2", city="t26-2-incl",
            health_status="hidden",
        )
        _aid, cookie = await seed_admin(session, "admin-incl@example.com")

    resp = await admin_resources_client.get(
        "/api/admin/resources?city=t26-2-incl&include_hidden=true",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    body = resp.json()
    assert body["total"] == 2
    assert {item["name"] for item in body["items"]} == {
        "visible-2", "hidden-2",
    }


@pytest.mark.anyio
async def test_list_pagination_offset_and_limit(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        for i in range(5):
            await seed_resource(
                session, name=f"P{i}", city="t26-2-page",
            )
        _aid, cookie = await seed_admin(session, "admin-page@example.com")

    resp = await admin_resources_client.get(
        "/api/admin/resources?city=t26-2-page&limit=2&offset=1",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    body = resp.json()
    assert body["limit"] == 2
    assert body["offset"] == 1
    assert body["total"] == 5
    assert len(body["items"]) == 2


@pytest.mark.anyio
async def test_list_limit_above_100_returns_422(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        _aid, cookie = await seed_admin(session, "admin-422@example.com")
    resp = await admin_resources_client.get(
        "/api/admin/resources?limit=500",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_list_filters_by_city(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        await seed_resource(
            session, name="FW-only", city="t26-2-cityA",
        )
        await seed_resource(
            session, name="DAL-only", city="t26-2-cityB",
        )
        _aid, cookie = await seed_admin(session, "admin-city@example.com")

    resp = await admin_resources_client.get(
        "/api/admin/resources?city=t26-2-cityA",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "FW-only"


# =====================================================================
# Cycle 3: get_resource
# =====================================================================


@pytest.mark.anyio
async def test_get_returns_resource(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        rid = await seed_resource(
            session, name="getme", city="t26-2-get",
        )
        _aid, cookie = await seed_admin(session, "admin-get@example.com")

    resp = await admin_resources_client.get(
        f"/api/admin/resources/{rid}",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == rid
    assert body["name"] == "getme"
    assert body["city"] == "t26-2-get"


@pytest.mark.anyio
async def test_get_unknown_returns_404(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        _aid, cookie = await seed_admin(session, "admin-404@example.com")
    resp = await admin_resources_client.get(
        "/api/admin/resources/99999",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 404


# =====================================================================
# Cycle 4: create_resource — stamps user_curated_at + returns id
# =====================================================================


@pytest.mark.anyio
async def test_create_returns_new_row_with_id(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        _aid, cookie = await seed_admin(session, "admin-create@example.com")

    resp = await admin_resources_client.post(
        "/api/admin/resources",
        json={
            "name": "Brand New",
            "category": "social_service",
            "city": "t26-2-create",
            "address": "100 Main St",
            "lat": 32.7,
            "lng": -97.3,
            "phone": "555-0100",
            "url": "https://example.com",
        },
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code in (200, 201), resp.text
    body = resp.json()
    assert "id" in body and isinstance(body["id"], int)
    assert body["name"] == "Brand New"
    assert body["city"] == "t26-2-create"

    # Verify DB row exists + user_curated_at stamped.
    async with session_factory() as session:
        row = await read_resource_row(session, body["id"])
        assert row is not None
        assert row["name"] == "Brand New"
        assert row["user_curated_at"] is not None


@pytest.mark.anyio
async def test_create_defaults_health_status_to_healthy(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        _aid, cookie = await seed_admin(session, "admin-create2@example.com")

    resp = await admin_resources_client.post(
        "/api/admin/resources",
        json={
            "name": "Default Health",
            "category": "social_service",
            "city": "t26-2-create2",
        },
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code in (200, 201), resp.text
    body = resp.json()
    async with session_factory() as session:
        row = await read_resource_row(session, body["id"])
        assert row["health_status"] == "healthy"


@pytest.mark.anyio
async def test_create_missing_required_returns_422(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        _aid, cookie = await seed_admin(session, "admin-422c@example.com")
    # Missing required ``name``.
    resp = await admin_resources_client.post(
        "/api/admin/resources",
        json={"category": "social_service", "city": "t26-2-create3"},
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 422


# =====================================================================
# Cycle 5: update_resource — stamps user_curated_at
# =====================================================================


@pytest.mark.anyio
async def test_patch_updates_fields_and_stamps_timestamp(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        rid = await seed_resource(
            session, name="OldName", city="t26-2-patch",
        )
        # Confirm seeded row has NULL user_curated_at to start.
        row_before = await read_resource_row(session, rid)
        assert row_before["user_curated_at"] is None
        _aid, cookie = await seed_admin(session, "admin-patch@example.com")

    resp = await admin_resources_client.patch(
        f"/api/admin/resources/{rid}",
        json={"name": "NewName", "phone": "555-9999"},
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200, resp.text

    async with session_factory() as session:
        row_after = await read_resource_row(session, rid)
        assert row_after["name"] == "NewName"
        assert row_after["user_curated_at"] is not None


@pytest.mark.anyio
async def test_patch_unknown_returns_404(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        _aid, cookie = await seed_admin(session, "admin-patch404@example.com")
    resp = await admin_resources_client.patch(
        "/api/admin/resources/99999",
        json={"name": "ghost"},
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 404


# =====================================================================
# Cycle 6: delete (soft-hide) + restore
# =====================================================================


@pytest.mark.anyio
async def test_delete_sets_health_status_hidden(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        rid = await seed_resource(
            session, name="ToHide", city="t26-2-del",
        )
        _aid, cookie = await seed_admin(session, "admin-del@example.com")

    resp = await admin_resources_client.delete(
        f"/api/admin/resources/{rid}",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code in (200, 204), resp.text

    async with session_factory() as session:
        row = await read_resource_row(session, rid)
        assert row is not None  # soft-delete: row still present
        assert row["health_status"] == "hidden"


@pytest.mark.anyio
async def test_restore_sets_health_status_healthy(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        rid = await seed_resource(
            session, name="ToRestore", city="t26-2-restore",
            health_status="hidden",
        )
        _aid, cookie = await seed_admin(session, "admin-restore@example.com")

    resp = await admin_resources_client.post(
        f"/api/admin/resources/{rid}/restore",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["health_status"] == "healthy"

    async with session_factory() as session:
        row = await read_resource_row(session, rid)
        assert row["health_status"] == "healthy"


@pytest.mark.anyio
async def test_delete_unknown_returns_404(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        _aid, cookie = await seed_admin(session, "admin-del404@example.com")
    resp = await admin_resources_client.delete(
        "/api/admin/resources/99999",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_restore_unknown_returns_404(
    admin_resources_client, session_factory
):
    async with session_factory() as session:
        _aid, cookie = await seed_admin(session, "admin-r404@example.com")
    resp = await admin_resources_client.post(
        "/api/admin/resources/99999/restore",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 404
