"""Defensive deserialization for resource columns coming back from SQLite.

The runtime stores ``services`` and ``barrier_affinity`` as JSON-encoded TEXT
in SQLite (no native JSON type).  The engine's ``query_resources_for_barriers``
hydrates these back into Python lists.  If a row ships with malformed JSON
(stale seed, manual SQL touch-up, future migration mismatch), the entire
assessment must NOT 500 — it should degrade to an empty list for that field
and continue serving the rest of the resources.

This file owns the regressive contract: malformed JSON in either field is
recoverable; the user still gets a plan.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.matching.engine import query_resources_for_barriers
from app.modules.matching.types import BarrierType


_CATS_PATCH = "app.modules.matching.engine.get_resources_by_categories"


def _row(**overrides) -> dict:
    base = {
        "id": 1,
        "name": "Career Center",
        "category": "career_center",
        "subcategory": None,
        "address": None,
        "lat": None,
        "lng": None,
        "phone": None,
        "url": None,
        "eligibility": None,
        "services": None,
        "hours": None,
        "notes": None,
        "barrier_affinity": None,
    }
    base.update(overrides)
    return base


class TestBarrierAffinityDeserialization:
    @pytest.mark.asyncio
    async def test_null_barrier_affinity_becomes_empty_list(self) -> None:
        row = _row(id=1, name="A", barrier_affinity=None)
        mock_session = AsyncMock()

        async def stub(_s, _c, city=None):
            return [row]

        with patch(_CATS_PATCH, side_effect=stub):
            result = await query_resources_for_barriers(
                [BarrierType.CREDIT], mock_session,
            )

        assert len(result) == 1
        assert result[0].barrier_affinity == []

    @pytest.mark.asyncio
    async def test_valid_json_string_decoded(self) -> None:
        row = _row(id=2, name="B", barrier_affinity='["transportation","training"]')
        mock_session = AsyncMock()

        async def stub(_s, _c, city=None):
            return [row]

        with patch(_CATS_PATCH, side_effect=stub):
            result = await query_resources_for_barriers(
                [BarrierType.CREDIT], mock_session,
            )

        assert result[0].barrier_affinity == ["transportation", "training"]

    @pytest.mark.asyncio
    async def test_malformed_json_string_falls_back_to_empty(self) -> None:
        """Garbage JSON must not 500 the assessment."""
        row = _row(id=3, name="C", barrier_affinity='not-json{[')
        mock_session = AsyncMock()

        async def stub(_s, _c, city=None):
            return [row]

        with patch(_CATS_PATCH, side_effect=stub):
            result = await query_resources_for_barriers(
                [BarrierType.CREDIT], mock_session,
            )

        assert len(result) == 1
        assert result[0].barrier_affinity == []

    @pytest.mark.asyncio
    async def test_malformed_services_json_falls_back_to_empty(self) -> None:
        """Same defensive treatment for the services column."""
        row = _row(id=4, name="D", services='not-json{[')
        mock_session = AsyncMock()

        async def stub(_s, _c, city=None):
            return [row]

        with patch(_CATS_PATCH, side_effect=stub):
            result = await query_resources_for_barriers(
                [BarrierType.CREDIT], mock_session,
            )

        assert len(result) == 1
        # services accepts None or list; degraded form is None for stricter typing
        assert result[0].services in (None, [])

    @pytest.mark.asyncio
    async def test_already_decoded_list_passes_through(self) -> None:
        """If a caller pre-decoded the list (test path), keep it."""
        row = _row(id=5, name="E", barrier_affinity=["criminal_record"])
        mock_session = AsyncMock()

        async def stub(_s, _c, city=None):
            return [row]

        with patch(_CATS_PATCH, side_effect=stub):
            result = await query_resources_for_barriers(
                [BarrierType.CREDIT], mock_session,
            )

        assert result[0].barrier_affinity == ["criminal_record"]
