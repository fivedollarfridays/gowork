"""Tests for the plan PDF endpoint + markdown composer."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.modules.plan.plan_pdf_composer import compose_plan_markdown


_VALID_UUID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
_VALIDATE_TOKEN_PATCH = "app.core.auth.validate_token"
_TOKEN_EXISTS_PATCH = "app.core.auth.token_exists"


def _token_query(session_id: str) -> str:
    return f"?token=test-token-{session_id}"


@pytest.fixture(autouse=True)
def _mock_token_validation():
    async def _validate(db, token):
        if token.startswith("test-token-"):
            return token.removeprefix("test-token-")
        return None

    async def _exists(db, token):
        return False

    with (
        patch(_VALIDATE_TOKEN_PATCH, side_effect=_validate),
        patch(_TOKEN_EXISTS_PATCH, side_effect=_exists),
    ):
        yield


def _seed_session_row(plan_dict: dict | None = None) -> dict:
    import json

    p = plan_dict or {
        "barriers": [],
        "job_matches": [],
        "immediate_next_steps": [],
        "action_plan": {
            "assessment_date": "2026-05-02",
            "phases": [],
            "total_actions": 0,
        },
        "resident_summary": "Demo summary.",
    }
    profile = {
        "session_id": _VALID_UUID,
        "zip_code": "76105",
        "primary_barriers": ["transportation"],
        "barrier_severity": "medium",
        "transit_dependent": True,
    }
    return {
        "id": _VALID_UUID,
        "plan": json.dumps(p),
        "barriers": json.dumps([]),
        "qualifications": "Forklift operator",
        "profile": json.dumps(profile),
        "credit_profile": None,
        "action_checklist": None,
    }


# ---------------------------------------------------------------------------
# Markdown composer — pure unit tests
# ---------------------------------------------------------------------------


class TestComposePlanMarkdown:
    def _plan(self, **overrides):
        base = {
            "resident_summary": (
                "You have already taken a big step. Your first step Monday "
                "morning is to reach out to TWC Child Care Subsidy."
            ),
            "barriers": ["transportation", "childcare"],
            "job_matches": [
                {
                    "title": "Wastewater Operator Trainee",
                    "company": "Trinity River Authority",
                    "location": "Arlington, TX 76011",
                    "pay_range": "$20.50/hr",
                    "relevance_score": 0.80,
                    "fair_chance": True,
                    "transit_accessible": False,
                },
                {
                    "title": "Warehouse Associate",
                    "company": "Goodwill",
                    "location": "Fort Worth, TX 76110",
                    "pay_range": "$14.00/hr",
                    "relevance_score": 0.78,
                    "fair_chance": True,
                    "transit_accessible": True,
                },
            ],
            "immediate_next_steps": [
                "Workforce Solutions for Tarrant County, 817-413-4400",
                "Contact TWC Child Care Subsidy (817-413-4400) for childcare support",
            ],
            "action_plan": {
                "assessment_date": "2026-05-02",
                "phases": [
                    {
                        "phase_id": "week_1_2",
                        "label": "Week 1-2: Immediate Actions",
                        "start_day": 0,
                        "end_day": 14,
                        "actions": [
                            {"category": "career_center", "title": "Visit Workforce Solutions"},
                            {"category": "job_application", "title": "Apply to Wastewater Operator"},
                        ],
                    },
                    {
                        "phase_id": "month_1",
                        "label": "Month 1: Foundations",
                        "start_day": 14, "end_day": 30,
                        "actions": [
                            {"category": "childcare", "title": "Follow up with TWC Child Care Subsidy"},
                        ],
                    },
                    {
                        "phase_id": "month_2_3",
                        "label": "Month 2-3: Building",
                        "start_day": 30, "end_day": 90,
                        "actions": [],
                    },
                ],
                "total_actions": 3,
            },
        }
        base.update(overrides)
        return base

    def _profile(self, **overrides):
        base = {
            "zip_code": "76105",
            "primary_barriers": ["transportation", "childcare"],
            "barrier_severity": "high",
            "transit_dependent": True,
        }
        base.update(overrides)
        return base

    def test_includes_h1_title(self):
        md = compose_plan_markdown(self._plan(), self._profile())
        assert md.lstrip().startswith("# "), "must lead with H1 for PDF title extraction"

    def test_starts_with_resident_summary(self):
        md = compose_plan_markdown(self._plan(), self._profile())
        assert "You have already taken a big step" in md

    def test_lists_top_jobs(self):
        md = compose_plan_markdown(self._plan(), self._profile())
        assert "Wastewater Operator Trainee" in md
        assert "Trinity River Authority" in md
        assert "$20.50/hr" in md

    def test_marks_fair_chance_badge(self):
        md = compose_plan_markdown(self._plan(), self._profile())
        assert "Fair Chance" in md or "fair-chance" in md.lower()

    def test_includes_action_plan_phases_only_nonempty(self):
        md = compose_plan_markdown(self._plan(), self._profile())
        assert "Week 1-2: Immediate Actions" in md
        assert "Month 1: Foundations" in md
        # month_2_3 has no actions — must be filtered
        assert "Month 2-3: Building" not in md

    def test_includes_immediate_next_steps(self):
        md = compose_plan_markdown(self._plan(), self._profile())
        assert "Workforce Solutions for Tarrant County" in md
        assert "TWC Child Care Subsidy" in md

    def test_no_doubled_support_word(self):
        md = compose_plan_markdown(self._plan(), self._profile())
        assert "support support" not in md.lower()

    def test_handles_missing_narrative_gracefully(self):
        plan = self._plan(resident_summary=None)
        md = compose_plan_markdown(plan, self._profile())
        # Must still contain jobs + action plan + steps, no exception
        assert "Wastewater Operator" in md
        assert "Week 1-2" in md

    def test_handles_no_jobs(self):
        plan = self._plan(job_matches=[])
        md = compose_plan_markdown(plan, self._profile())
        # Top Job Matches section must be omitted entirely
        assert "## Top Job Matches" not in md
        # Other sections still render
        assert "Week 1-2" in md
        assert "## Immediate Next Steps" in md

    def test_no_alabama_leak(self):
        md = compose_plan_markdown(self._plan(), self._profile())
        for term in ("Montgomery", "Alabama", "OneAlabama", "MATS", "Trenholm"):
            assert term not in md, f"AL leak: {term}"


# ---------------------------------------------------------------------------
# Route — GET /api/plan/{session_id}/pdf
# ---------------------------------------------------------------------------


_GET_SESSION_PATCH = "app.routes.plan.get_session_by_id"
_RENDER_PDF_PATCH = "app.routes.plan.render_markdown_to_pdf"


class TestPlanPdfRoute:
    @pytest.mark.asyncio
    async def test_returns_application_pdf_content_type(self):
        row = _seed_session_row()
        with (
            patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row),
            patch(_RENDER_PDF_PATCH, return_value=b"%PDF-1.4 stub"),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(
                    f"/api/plan/{_VALID_UUID}/pdf{_token_query(_VALID_UUID)}",
                )
        assert resp.status_code == 200, resp.text
        assert resp.headers["content-type"].startswith("application/pdf")
        assert resp.content.startswith(b"%PDF-")

    @pytest.mark.asyncio
    async def test_includes_attachment_disposition(self):
        row = _seed_session_row()
        with (
            patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row),
            patch(_RENDER_PDF_PATCH, return_value=b"%PDF-1.4"),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(
                    f"/api/plan/{_VALID_UUID}/pdf{_token_query(_VALID_UUID)}",
                )
        cd = resp.headers.get("content-disposition", "")
        assert "attachment" in cd.lower()
        assert ".pdf" in cd.lower()

    @pytest.mark.asyncio
    async def test_404_when_session_missing(self):
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=None):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(
                    f"/api/plan/{_VALID_UUID}/pdf{_token_query(_VALID_UUID)}",
                )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_500_when_pdf_renderer_fails(self):
        from app.core.pdf_renderer import PdfRenderError

        row = _seed_session_row()
        with (
            patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row),
            patch(_RENDER_PDF_PATCH, side_effect=PdfRenderError("WeasyPrint deps missing")),
        ):
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(
                    f"/api/plan/{_VALID_UUID}/pdf{_token_query(_VALID_UUID)}",
                )
        assert resp.status_code == 500
