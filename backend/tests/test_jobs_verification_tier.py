"""Public listing fetch verification-tier extension (T24.6).

The `GET /api/jobs` endpoint is the candidate-facing read for the
job-listing surface. T24.6 extends every job dict with a `verification`
field projected from the `listing_verifications` table:

    {tier: str, verified_at: str, intake_complete: bool} | null

Critical invariants pinned here:

* `intake_json` is NEVER on the public payload — only the boolean
  `intake_complete` derived from `intake_completed_at IS NOT NULL`. A
  canary string seeded into the intake blob asserts the leak doesn't
  silently regress.
* The verification join goes through one batched call to
  `get_public_verification_summary(listing_ids)` — single query, no
  N+1 fanout.
* `Cache-Control: public, max-age=60` mirrors the assessments public
  endpoint (T23.6) — the verification tier is stable enough for a
  one-minute edge cache.
* Anonymous-first: the route still works without auth and returns the
  same shape regardless of session binding.

The route already has its own dedicated test (``test_jobs_route.py``)
covering filters / rate limits / shape; this module focuses ONLY on
the verification extension.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


_AGG_SEARCH_PATCH = "app.integrations.job_aggregator.JobAggregator.search"
_EMPLOYERS_PATCH = "app.routes.jobs.get_all_employers"
_TRANSIT_PATCH = "app.routes.jobs.get_all_transit_routes"
_VERIFICATION_PATCH = "app.routes.jobs.get_public_verification_summary"


def _sample_jobs() -> list[dict]:
    """Three listings with stable ids; mirrors test_jobs_route.py shape."""
    return [
        {
            "id": 1, "title": "CNA", "company": "Baptist Hospital",
            "location": "Montgomery, AL", "description": "Nursing",
            "url": "https://example.com/cna", "source": "seed",
            "scraped_at": "2026-03-01", "expires_at": None,
        },
        {
            "id": 2, "title": "Warehouse", "company": "Amazon",
            "location": "Montgomery, AL", "description": "Warehouse work",
            "url": "https://example.com/wh", "source": "seed",
            "scraped_at": "2026-03-01", "expires_at": None,
        },
        {
            "id": 3, "title": "Teller", "company": "Regions Bank",
            "location": "Montgomery, AL", "description": "Customer svc",
            "url": "https://example.com/teller", "source": "seed",
            "scraped_at": "2026-03-01", "expires_at": None,
        },
    ]


def _sample_employers() -> list[dict]:
    return [
        {"name": "Baptist Hospital", "industry": "healthcare",
         "license_type": None, "lat": 32.36, "lng": -86.27},
        {"name": "Amazon", "industry": "logistics",
         "license_type": None, "lat": 32.38, "lng": -86.35},
        {"name": "Regions Bank", "industry": "finance",
         "license_type": "banking", "lat": 32.37, "lng": -86.30},
    ]


def _verification_summary_two_verified() -> dict[int, dict]:
    """Two of the three sample listings are verified; one is not.

    Listing 1 — source_trust, intake not done.
    Listing 2 — claim_verified, intake DONE.
    Listing 3 — NOT in the dict (no verification row).
    """
    return {
        1: {
            "verification_tier": "source_trust",
            "employer_account_id": 11,
            "intake_complete": False,
            "verified_at": "2026-05-01T00:00:00Z",
        },
        2: {
            "verification_tier": "claim_verified",
            "employer_account_id": 22,
            "intake_complete": True,
            "verified_at": "2026-05-02T00:00:00Z",
        },
    }


async def _get_jobs(verification_summary: dict[int, dict]) -> tuple[int, dict, dict]:
    """Hit GET /api/jobs/ with all five collaborators mocked.

    Returns (status_code, json_body, headers_dict).
    """
    from app.main import app
    from app.routes.jobs import _list_rate_limiter

    _list_rate_limiter.clear()
    with (
        patch(_AGG_SEARCH_PATCH, new_callable=AsyncMock,
              return_value=_sample_jobs()),
        patch(_EMPLOYERS_PATCH, new_callable=AsyncMock,
              return_value=_sample_employers()),
        patch(_TRANSIT_PATCH, new_callable=AsyncMock, return_value=[]),
        patch(_VERIFICATION_PATCH, new_callable=AsyncMock,
              return_value=verification_summary) as mock_summary,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            resp = await c.get("/api/jobs/")
        # Assert the batched read was called exactly once (no N+1).
        assert mock_summary.call_count == 1, (
            f"Expected 1 call to get_public_verification_summary, "
            f"got {mock_summary.call_count}"
        )
    _list_rate_limiter.clear()
    return resp.status_code, resp.json(), dict(resp.headers)


# ---------------------------------------------------------------- tests


class TestVerificationFieldShape:
    """The `verification` field is present on every job in the response."""

    @pytest.mark.asyncio
    async def test_unverified_listing_returns_verification_null(self):
        """Listings not in the summary dict get `verification: null`."""
        status, body, _ = await _get_jobs(_verification_summary_two_verified())
        assert status == 200
        unverified = next(j for j in body["jobs"] if j["id"] == 3)
        assert "verification" in unverified
        assert unverified["verification"] is None

    @pytest.mark.asyncio
    async def test_source_trust_tier_surfaces_in_response(self):
        """source_trust tier returns tier + verified_at + intake_complete=False."""
        status, body, _ = await _get_jobs(_verification_summary_two_verified())
        assert status == 200
        listing_one = next(j for j in body["jobs"] if j["id"] == 1)
        assert listing_one["verification"] == {
            "tier": "source_trust",
            "verified_at": "2026-05-01T00:00:00Z",
            "intake_complete": False,
        }

    @pytest.mark.asyncio
    async def test_claim_verified_with_intake_complete_true(self):
        """claim_verified + intake done → intake_complete: true."""
        status, body, _ = await _get_jobs(_verification_summary_two_verified())
        assert status == 200
        listing_two = next(j for j in body["jobs"] if j["id"] == 2)
        assert listing_two["verification"]["tier"] == "claim_verified"
        assert listing_two["verification"]["intake_complete"] is True


class TestIntegrityInvariants:
    """Charter-level guards: no PII leak, no N+1, consistent caching."""

    @pytest.mark.asyncio
    async def test_intake_json_canary_never_leaks_to_response(self):
        """Even if upstream summary leaks intake_json, route MUST strip it.

        The queries-layer helper already excludes ``intake_json`` from
        its return shape, but a future regression there shouldn't
        cascade into a candidate-facing leak. Seed the verification
        summary with a forbidden ``intake_json`` carrying a unique
        canary; assert the canary bytes never appear anywhere in the
        serialized response body.
        """
        canary = "CANARY-INTAKE-LEAK-7c4f9a1e-DO-NOT-LEAK"
        leaky_summary = {
            1: {
                "verification_tier": "claim_verified",
                "employer_account_id": 11,
                "intake_complete": True,
                "verified_at": "2026-05-01T00:00:00Z",
                # Intentionally include intake_json — route must drop it.
                "intake_json": f'{{"secret_terms":"{canary}"}}',
            },
        }
        status, body, _ = await _get_jobs(leaky_summary)
        assert status == 200
        # Re-serialize the body and scan bytes for the canary.
        import json as _json
        serialized = _json.dumps(body)
        assert canary not in serialized, (
            "intake_json canary leaked into the public /api/jobs payload"
        )
        # And no `intake_json` key on any listing.
        for job in body["jobs"]:
            v = job.get("verification")
            if v is not None:
                assert "intake_json" not in v, (
                    f"intake_json key surfaced on listing {job['id']}"
                )

    @pytest.mark.asyncio
    async def test_cache_control_header_set(self):
        """Successful 200 sets `Cache-Control: public, max-age=60`."""
        _, _, headers = await _get_jobs(_verification_summary_two_verified())
        assert headers.get("cache-control") == "public, max-age=60"

    @pytest.mark.asyncio
    async def test_anon_vs_claimed_session_returns_equivalent_shape(self):
        """Two callers (one would-be claimed, one anon) get same body.

        /api/jobs takes no session id, so a "claimed" caller is just a
        second invocation of the same anonymous route — but the test
        still pins the shape-equivalence promise: changing the route to
        gate on auth would make this fail loudly.
        """
        # Run the request twice with identical inputs; bodies must match.
        s1, b1, h1 = await _get_jobs(_verification_summary_two_verified())
        s2, b2, h2 = await _get_jobs(_verification_summary_two_verified())
        assert s1 == s2 == 200
        assert b1 == b2
        assert h1.get("cache-control") == h2.get("cache-control")
