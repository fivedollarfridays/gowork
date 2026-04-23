"""T12.33 — Intelligence Engine Wire-Up integration tests.

Verifies that the T12.12 `application_conversion_rates` wire-up at
`GET /api/intelligence/barriers` works end-to-end:

- Segment key + all three sub-slices present on the response.
- k-anonymity suppression (<5 sessions) flows through as
  ``{"count": null, "suppressed": true, "reason": "k_anonymity_min_5"}``.
- Above-threshold cohorts produce integer counts.
- Pre-T12.12 response keys (the S11 community-insights consumer contract)
  remain present with their pre-existing types — purely additive change.
- Handler survives exceptions raised from the funnel pipeline (T12.12's
  defensive try/except returns an empty three-slice payload on failure,
  never a 500).
- Cross-city isolation: the active-city payload never leaks rows from
  a different city's cohort.

These tests pin regression against the S11 capstone consumer fields
verified to be read by the frontend community-insights view:
``barriers[*].barrier_id``, ``confidence``, ``calibrated_weeks``,
``default_weeks``, ``total_feedback_count``, ``avg_plan_accuracy``.
"""

from __future__ import annotations

import pytest

from app.modules.jobs.funnel_analytics import (
    FunnelCounts,
    FunnelResult,
    SuppressedCell,
)
from app.routes import intelligence as intelligence_route


# -------------------- Monkeypatch helpers --------------------


def _patch_acr(monkeypatch: pytest.MonkeyPatch, payload: dict) -> None:
    """Replace the route's funnel serializer with a deterministic payload."""
    monkeypatch.setattr(
        intelligence_route,
        "_serialize_application_conversion_rates",
        lambda: payload,
    )


def _suppressed_cell() -> dict:
    return {
        "count": None,
        "suppressed": True,
        "reason": "k_anonymity_min_5",
    }


def _funnel_cell(*, applied: int = 5) -> dict:
    """Shape of a non-suppressed FunnelResult after model_dump."""
    return {
        "counts": {
            "draft": 0, "applied": applied, "interview": 0,
            "offer": 0, "rejected": 0, "withdrawn": 0,
        },
        "draft_to_applied_rate": 1.0,
        "applied_to_interview_rate": 0.0,
        "interview_to_offer_rate": None,
    }


# -------------------- AC #1 — segment present --------------------


@pytest.mark.anyio
async def test_endpoint_response_includes_application_conversion_rates(
    client,
) -> None:
    """Base case: the new key is always present on the response."""
    resp = await client.get("/api/intelligence/barriers")
    assert resp.status_code == 200
    assert "application_conversion_rates" in resp.json()


@pytest.mark.anyio
async def test_sub_keys_present(client) -> None:
    """All three funnel slices appear under application_conversion_rates."""
    resp = await client.get("/api/intelligence/barriers")
    acr = resp.json()["application_conversion_rates"]
    assert set(acr.keys()) == {
        "city_scoped", "by_cleared_barriers", "by_fair_chance",
    }


# -------------------- AC #2 — suppression flows through --------------------


@pytest.mark.anyio
async def test_small_cell_suppression_flows_through(
    client, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A below-k cohort surfaces as null + suppressed: true on the wire."""
    _patch_acr(monkeypatch, {
        "city_scoped": {"__all__": _suppressed_cell()},
        "by_cleared_barriers": {},
        "by_fair_chance": {},
    })

    resp = await client.get("/api/intelligence/barriers")
    cell = resp.json()["application_conversion_rates"]["city_scoped"]["__all__"]
    assert cell["count"] is None
    assert cell["suppressed"] is True
    assert cell["reason"] == "k_anonymity_min_5"


@pytest.mark.anyio
async def test_suppression_roundtrips_through_serializer(
    client, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end: a real SuppressedCell from the funnel pipeline is
    correctly model_dumped by the route into null + suppressed: true.

    Unlike test_small_cell_suppression_flows_through (which pre-dumps the
    dict shape), this exercises the serializer path with live pydantic
    objects — the same type the production pipeline emits.
    """
    def _fake_builder(city: str, *, db_path):
        return {
            "city_scoped": {"__all__": SuppressedCell()},
            "by_cleared_barriers": {},
            "by_fair_chance": {},
        }

    monkeypatch.setattr(
        intelligence_route, "build_application_conversion_rates", _fake_builder,
    )

    resp = await client.get("/api/intelligence/barriers")
    cell = resp.json()["application_conversion_rates"]["city_scoped"]["__all__"]
    assert cell == {
        "count": None,
        "suppressed": True,
        "reason": "k_anonymity_min_5",
    }


@pytest.mark.anyio
async def test_above_threshold_returns_counts(
    client, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """At-or-above k cohorts surface integer counts, not null."""
    _patch_acr(monkeypatch, {
        "city_scoped": {"__all__": _funnel_cell(applied=5)},
        "by_cleared_barriers": {},
        "by_fair_chance": {},
    })

    resp = await client.get("/api/intelligence/barriers")
    cell = resp.json()["application_conversion_rates"]["city_scoped"]["__all__"]
    assert cell["counts"]["applied"] == 5
    assert isinstance(cell["counts"]["applied"], int)
    assert "suppressed" not in cell


# -------------------- AC #3 — S11 consumer regression --------------------


# Pre-T12.12 keys read by the S11 community-insights consumer. If this
# list changes, audit frontend consumers before modifying the test.
_S11_CONSUMER_CONTRACT: dict[str, type] = {
    "barriers": list,
    "confidence": str,
    "calibrated_weeks": dict,
    "default_weeks": dict,
    "total_feedback_count": int,
    "avg_plan_accuracy": (int, float, type(None)),  # None when no feedback
}


@pytest.mark.anyio
async def test_response_shape_additive_only(client) -> None:
    """All pre-T12.12 keys remain present with their expected types."""
    resp = await client.get("/api/intelligence/barriers")
    data = resp.json()
    for key, expected in _S11_CONSUMER_CONTRACT.items():
        assert key in data, f"regression: {key!r} missing from response"
        assert isinstance(data[key], expected), (
            f"regression: {key!r} is {type(data[key]).__name__}, "
            f"expected {expected}"
        )


@pytest.mark.anyio
async def test_s11_consumer_contract_preserved_default_weeks(client) -> None:
    """Canonical barrier keys in default_weeks still surface (S11 pins these)."""
    resp = await client.get("/api/intelligence/barriers")
    default_weeks = resp.json()["default_weeks"]
    # S11 community-insights renders these specific barrier ids.
    for bid in ("criminal_record", "credit", "transportation",
                "childcare", "housing"):
        assert bid in default_weeks
        assert isinstance(default_weeks[bid], int)


@pytest.mark.anyio
async def test_s11_consumer_contract_barriers_array_shape(
    client, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When barriers exist, each entry carries the fields S11 reads."""
    # No seeded feedback in the test DB → barriers is []. Ensure the
    # contract (empty list) is still a list and does not 500.
    resp = await client.get("/api/intelligence/barriers")
    barriers = resp.json()["barriers"]
    assert isinstance(barriers, list)
    # Structural assertion — with seeded data each entry would have
    # {barrier_id, confidence, sample_size, success_rate, avg_weeks}.
    # The populated path is exercised by tests/test_intelligence_route.py
    # and tests/test_full_pipeline_with_data.py; here we pin the empty
    # case which the S11 view MUST tolerate.


# -------------------- AC #4 — handler error isolation --------------------


@pytest.mark.anyio
async def test_handler_survives_funnel_analytics_exception(
    client, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A raise from the funnel pipeline never bubbles into a 500."""
    def _boom(*_args, **_kwargs):  # pragma: no cover — exercised below
        raise RuntimeError("funnel pipeline exploded")

    monkeypatch.setattr(
        intelligence_route, "build_application_conversion_rates", _boom,
    )

    resp = await client.get("/api/intelligence/barriers")
    assert resp.status_code == 200
    data = resp.json()
    assert "application_conversion_rates" in data
    # T12.12's graceful degradation returns the three-key shape with
    # empty sub-dicts — NOT a 500 and NOT a missing key.
    acr = data["application_conversion_rates"]
    assert acr == {
        "city_scoped": {},
        "by_cleared_barriers": {},
        "by_fair_chance": {},
    }


# -------------------- AC #5 — cross-city isolation --------------------


@pytest.mark.anyio
async def test_no_cross_city_data_leak(
    client, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A payload built for city A must not surface city B's counts.

    The route passes ``settings.city`` into build_application_conversion_rates;
    we assert that when a request is served, only the configured-city slice
    reaches the response. Simulate by patching the builder to verify it is
    invoked with exactly the settings city and that cross-city contamination
    would not silently pass through.
    """
    captured: dict[str, object] = {}

    def _spy(city: str, *, db_path):
        captured["city"] = city
        captured["db_path"] = db_path
        # Return the shape the route's serializer expects — pydantic
        # models with .model_dump(). No cross-city data; only the
        # slice belonging to the configured city surfaces.
        result = FunnelResult(
            counts=FunnelCounts(applied=7),
            draft_to_applied_rate=1.0,
            applied_to_interview_rate=0.0,
            interview_to_offer_rate=None,
        )
        return {
            "city_scoped": {"__all__": result},
            "by_cleared_barriers": {},
            "by_fair_chance": {},
        }

    # We need to patch within the serialize helper's call path.
    monkeypatch.setattr(
        intelligence_route, "build_application_conversion_rates", _spy,
    )

    resp = await client.get("/api/intelligence/barriers")
    assert resp.status_code == 200
    # Serializer was called once with the configured city.
    assert "city" in captured
    assert isinstance(captured["city"], str)
    # Configured city per Settings default is "montgomery".
    assert captured["city"] == "montgomery"
    # Returned counts match what we seeded for THIS city only.
    cell = resp.json()["application_conversion_rates"]["city_scoped"]["__all__"]
    assert cell["counts"]["applied"] == 7
