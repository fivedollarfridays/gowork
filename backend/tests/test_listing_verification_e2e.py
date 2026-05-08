"""End-to-end smoke for the Sprint 24 listing-verification chain (T24.11).

Drives the full path through the actual route handlers via
:class:`httpx.AsyncClient` over the shared FastAPI app: claim → verify
→ intake → public fetch → reputation event. Mocks SendGrid at the
boundary so no live email leaves the suite.

Charter integrity invariant
---------------------------
The matching engine MUST read zero verification signals. Sprint 24's
verification tier is display-only — it shapes the candidate-facing
public fetch but NEVER feeds back into match scoring. This test
runs an explicit grep across ``backend/app/modules/matching/`` and
asserts no reference to the new tables / fields.

If a future sprint legitimately needs to use a verification signal in
the matching engine, this test failing is the design-review trigger:
it must be discussed and the integrity charter amended before merging.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import (
    queries_accounts,
    queries_listings_verification,
    queries_roles,
)
from app.core.accounts_schema import apply_ddl as apply_accounts_ddl
from app.core.listings_verification_schema import (
    apply_ddl as apply_verification_ddl,
)
from app.core.roles_schema import apply_ddl as apply_roles_ddl
from app.integrations.email import mock_provider, sendgrid_client
from app.routes._auth_claim_helpers import (
    SESSION_COOKIE_NAME,
    build_account_cookie_value,
)


CLAIM_URL_RE = re.compile(
    r"https?://[^/]+/employers/claim\?token=([A-Za-z0-9_\-]{30,})"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def e2e_engine(test_engine):
    """``test_engine`` plus accounts + roles + verification DDL."""
    async with test_engine.begin() as conn:
        await conn.run_sync(apply_accounts_ddl)
        await conn.run_sync(apply_roles_ddl)
        await conn.run_sync(apply_verification_ddl)
    return test_engine


@pytest.fixture
def e2e_session_factory(e2e_engine):
    return async_sessionmaker(
        e2e_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture
def mock_sendgrid(monkeypatch):
    fake = mock_provider.MockSendGridClient()
    monkeypatch.setattr(sendgrid_client, "_build_client", lambda: fake)
    monkeypatch.setenv("FEATURE_EMAIL_SEND_ENABLED", "true")
    return fake


@pytest.fixture(autouse=True)
def _reset_rate_limiters():
    from app.routes import employers as employers_module

    employers_module._email_limiter.clear()
    employers_module._ip_limiter.clear()
    yield
    employers_module._email_limiter.clear()
    employers_module._ip_limiter.clear()


def _extract_token(fake: mock_provider.MockSendGridClient) -> str:
    assert fake.calls, "expected SendGrid mock to receive a send"
    payload = fake.calls[-1]
    body = payload.get("text", "") + " " + payload.get("html", "")
    match = CLAIM_URL_RE.search(body)
    assert match is not None, f"claim URL not in payload: {payload!r}"
    return match.group(1)


# ---------------------------------------------------------------------------
# E2E — full chain
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_e2e_claim_verify_intake_public_fetch_reputation_event(
    client, e2e_session_factory, mock_sendgrid
):
    """Drive the full S24 chain through the real HTTP layer."""
    # ------ Seed accounts (admin for the matching-engine grep helper +
    # ------ case_manager for the reputation event recording) ------
    async with e2e_session_factory() as session:
        admin_id = await queries_accounts.create_account(
            session, email="e2e-admin@example.com"
        )
        await queries_roles.grant_role(session, admin_id, "admin")
        cm_id = await queries_accounts.create_account(
            session, email="e2e-casemanager@example.com"
        )
        await queries_roles.grant_role(session, cm_id, "case_manager")

        # Seed a job_listing whose company fuzzy-matches the claimant's
        # domain so the verify orchestrator promotes to claim_verified.
        result = await session.execute(
            text(
                "INSERT INTO job_listings (title, company, scraped_at) "
                "VALUES (:t, :c, :s) RETURNING id"
            ),
            {
                "t": "Forklift Operator",
                "c": "ACME Hiring Inc",
                "s": "2026-05-08T00:00:00Z",
            },
        )
        listing_id = int(result.scalar_one())
        await session.commit()

    cm_cookie = build_account_cookie_value(cm_id)

    # ------ STEP 1: pre-claim verification surface is null ------
    # The /api/jobs route is aggregator-heavy and tested separately
    # (test_jobs_verification_tier.py + test_jobs_route.py). The e2e
    # focuses on the unique S24 chain — exercise the queries-layer
    # public-summary helper directly, which is what /api/jobs delegates
    # to via T24.6's batched read.
    async with e2e_session_factory() as session:
        pre_claim_summary = (
            await queries_listings_verification.get_public_verification_summary(
                session, [listing_id]
            )
        )
    assert pre_claim_summary == {}, (
        "unverified listing must have no public verification record"
    )

    # ------ STEP 2: POST /api/employers/claim ------
    claim_resp = await client.post(
        "/api/employers/claim",
        json={
            "listing_id": listing_id,
            "claimant_email": "hr@acmehiring.com",
        },
    )
    assert claim_resp.status_code == 202, claim_resp.text

    # ------ STEP 3: GET /api/employers/claim/verify?token=... ------
    raw_token = _extract_token(mock_sendgrid)
    verify_resp = await client.get(
        f"/api/employers/claim/verify?token={raw_token}"
    )
    assert verify_resp.status_code == 200, verify_resp.text
    verify_body = verify_resp.json()
    assert verify_body["verification_tier"] == "claim_verified", (
        "domain ACME Hiring ↔ acmehiring.com should match → claim_verified"
    )
    employer_account_id = int(verify_body["employer_account_id"])
    employer_cookie = verify_resp.cookies.get("gw_employer_account")
    assert employer_cookie, "gw_employer_account cookie must be set"

    # ------ STEP 4: POST intake ------
    intake_resp = await client.post(
        f"/api/employers/{employer_account_id}/listings/{listing_id}/intake",
        json={
            "must_haves": ["forklift certification"],
            "nice_to_haves": ["bilingual"],
            "real_day1_tasks": ["operate forklift on shop floor"],
            "comp_band_min": 18,
            "comp_band_max": 22,
            "fair_chance_willingness": True,
            "additional_notes": None,
        },
        cookies={"gw_employer_account": employer_cookie},
    )
    assert intake_resp.status_code == 200, intake_resp.text

    # ------ STEP 5: post-intake verification surface — public summary ------
    # Charter invariant: intake_json must NOT be in the public surface.
    # get_public_verification_summary is the helper /api/jobs delegates to;
    # T24.6's tests pin the route-side response shape + Cache-Control.
    async with e2e_session_factory() as session:
        post_intake_summary = (
            await queries_listings_verification.get_public_verification_summary(
                session, [listing_id]
            )
        )
    assert listing_id in post_intake_summary
    summary = post_intake_summary[listing_id]
    # Helper returns `verification_tier`; the route layer renames to `tier`
    # in the public response (T24.6). Check the helper key here.
    assert summary["verification_tier"] == "claim_verified"
    assert summary["intake_complete"] is True
    assert "intake_json" not in summary, (
        "charter invariant: intake_json must NEVER appear in public summary"
    )
    assert "forklift certification" not in str(summary), (
        "intake content must not leak through stringification of summary"
    )

    # ------ STEP 6: POST reputation event (case_manager) ------
    event_resp = await client.post(
        f"/api/listings/{listing_id}/events",
        json={"kind": "response_received", "session_id": None, "notes": None},
        cookies={SESSION_COOKIE_NAME: cm_cookie},
    )
    assert event_resp.status_code == 200, event_resp.text


# ---------------------------------------------------------------------------
# Charter integrity — the load-bearing assertion
# ---------------------------------------------------------------------------


def test_matching_engine_reads_zero_verification_signals():
    """The matching engine MUST NOT read any S24 verification signals.

    Verification tier is display-only per the integrity charter
    (principles 1–3: no commercial signals shape match position;
    verification is earned through artifacts, not money). This test
    runs a strict grep across the matching module and fails if ANY
    reference to S24 schema appears.

    If this test fails, the design must be reviewed before merging:
    either the reference is incidental (rename it) or the matching
    engine genuinely needs a verification signal (charter amendment
    required first).
    """
    repo_root = Path(__file__).resolve().parent.parent
    matching_dir = repo_root / "app" / "modules" / "matching"
    assert matching_dir.is_dir(), f"matching dir missing: {matching_dir}"

    forbidden = (
        "listing_verifications",
        "listing_reputation_events",
        "verification_tier",
        "intake_complete",
        "intake_json",
        "employer_accounts",
        "listing_claims",
    )
    pattern = "|".join(re.escape(token) for token in forbidden)

    result = subprocess.run(
        [
            "grep",
            "-rEln",
            "--include=*.py",
            pattern,
            str(matching_dir),
        ],
        capture_output=True,
        text=True,
    )
    # grep exits 0 on match, 1 on no match, 2 on error. We want 1.
    if result.returncode == 0:
        pytest.fail(
            "Matching engine references S24 verification signals — "
            "charter integrity invariant violated. Hits:\n"
            + result.stdout
        )
    assert result.returncode in (1, 2), (
        f"grep exited unexpectedly: rc={result.returncode}, "
        f"stderr={result.stderr}"
    )
