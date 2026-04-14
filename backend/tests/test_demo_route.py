"""Tests for the demo seed admin endpoint.

Cycle 3: POST /api/demo/seed protected by admin key.
"""

import pytest


class TestDemoSeedEndpoint:
    """POST /api/demo/seed should require admin key and seed data."""

    @pytest.mark.anyio
    async def test_seed_requires_admin_key(self, client, test_engine):
        """Endpoint should reject requests without admin key."""
        r = await client.post("/api/demo/seed")
        assert r.status_code == 403

    @pytest.mark.anyio
    async def test_seed_rejects_wrong_key(self, client, test_engine):
        """Endpoint should reject requests with wrong admin key."""
        r = await client.post(
            "/api/demo/seed",
            headers={"X-Admin-Key": "wrong-key"},
        )
        assert r.status_code == 403

    @pytest.mark.anyio
    async def test_seed_succeeds_with_correct_key(self, client, test_engine):
        """Endpoint should succeed and return summary with correct key."""
        r = await client.post(
            "/api/demo/seed",
            headers={"X-Admin-Key": "montgowork-demo-2026"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["sessions_created"] == 50
        assert data["feedback_created"] == 30

    @pytest.mark.anyio
    async def test_seed_is_idempotent_message(self, client, test_engine):
        """Second seed attempt should indicate data already exists."""
        # First seed
        r1 = await client.post(
            "/api/demo/seed",
            headers={"X-Admin-Key": "montgowork-demo-2026"},
        )
        assert r1.status_code == 200

        # Second seed — should return already-seeded message
        r2 = await client.post(
            "/api/demo/seed",
            headers={"X-Admin-Key": "montgowork-demo-2026"},
        )
        assert r2.status_code == 200
        assert r2.json().get("already_seeded") is True
