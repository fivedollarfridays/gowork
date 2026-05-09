"""Integration test: T26.1 loader-respect contract (T26.2).

Standalone file so the main :mod:`tests.test_admin_resources` suite
stays under the architecture warning thresholds. The contract under
test:

  Re-running ``seed_from_file`` against a row whose ``user_curated_at``
  was stamped by ``create_resource`` MUST NOT overwrite that row — the
  loader skips ``(city, name)`` pairs whose existing row carries a
  non-NULL curation marker.

This is the cross-task gate between T26.1 (column + loader skip logic)
and T26.2 (CRUD writers that stamp the column).
"""

from __future__ import annotations

import json

import pytest

from app.core.seed_helpers import seed_from_file
from app.routes._auth_claim_helpers import SESSION_COOKIE_NAME
from tests._admin_resources_helpers import (
    read_resource_row,
    seed_admin,
)


# Register the helpers module as a pytest plugin so its fixtures
# (resources_engine, session_factory, admin_resources_client) are
# discovered by name without colliding with the function-arg
# rebindings ruff flags as F811.
pytest_plugins = ["tests._admin_resources_helpers"]


async def _create_curated_row(
    client, cookie: str, *, city: str, phone: str
) -> int:
    resp = await client.post(
        "/api/admin/resources",
        json={
            "name": "Curated Row",
            "category": "social_service",
            "city": city,
            "phone": phone,
        },
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code in (200, 201), resp.text
    return int(resp.json()["id"])


@pytest.mark.anyio
async def test_seed_does_not_overwrite_curated_row(
    admin_resources_client, session_factory, tmp_path, resources_engine
):
    """Re-seed against an admin-created row — phone MUST stay admin-edited."""
    async with session_factory() as session:
        _aid, cookie = await seed_admin(session, "admin-seed@example.com")

    rid = await _create_curated_row(
        admin_resources_client, cookie,
        city="t26-2-seed-respect", phone="ADMIN-EDIT",
    )

    # Write the conflicting seed file with a different phone value.
    seed_payload = [{
        "name": "Curated Row",
        "category": "social_service",
        "city": "t26-2-seed-respect",
        "phone": "SEED-OVERWRITE",
    }]
    seed_file = tmp_path / "resources.json"
    seed_file.write_text(json.dumps(seed_payload))

    # Re-run the loader against the same engine.
    async with resources_engine.begin() as conn:
        await seed_from_file(
            conn, seed_file, "resources",
            city_slug="t26-2-seed-respect",
        )

    async with session_factory() as session:
        row = await read_resource_row(session, rid)
        assert row is not None
        assert row["phone"] == "ADMIN-EDIT", (
            f"Curated row was overwritten by seed: {row}"
        )
