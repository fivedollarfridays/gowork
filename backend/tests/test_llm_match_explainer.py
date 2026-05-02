"""Tests for the Haiku-augmented "Explain My Match" composer."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.integrations.llm import _cache, match_explainer
from app.integrations.llm._haiku_client import HaikuError, HaikuResult


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    _cache.match_explanation_cache.clear()


_BASE_JOB = {
    "title": "Certified Nursing Assistant",
    "company": "Texas Health Resources",
    "url": "https://example.com/cna-1",
    "location": "Fort Worth, TX",
}
_BREAKDOWN = {
    "skills": 0.55, "title_family": 0.80, "industry": 0.70,
    "years": 0.40, "education": 0.20, "certifications": 0.60,
    "industry_aligned": True,
}
_DOCS = [
    {"title": "Trinity Metro CNA Bus Pass Program",
     "text": "Trinity Metro provides discounted bus passes for CNAs commuting to Fort Worth healthcare facilities."},
    {"title": "Workforce Solutions for Tarrant County",
     "text": "WSTC at 1200 Circle Dr offers direct intros to healthcare employers."},
]


class TestExplainMatchHappyPath:
    @pytest.mark.asyncio
    async def test_haiku_success_returns_text_and_caches(self) -> None:
        """Successful Haiku call returns text and primes cache."""
        fake = HaikuResult(
            text="You're a strong fit. Visit Trinity Metro Monday.",
            input_tokens=600, output_tokens=80,
        )
        with patch.object(
            match_explainer, "call_haiku", AsyncMock(return_value=fake),
        ) as mock_call:
            out = await match_explainer.explain_match(
                session_id="sess-1", job=_BASE_JOB,
                score_breakdown=_BREAKDOWN, barriers=["TRANSIT"],
                retrieved_docs=_DOCS,
            )
        assert out["source"] == "haiku"
        assert out["cached"] is False
        assert "Trinity Metro" in out["text"]
        assert mock_call.call_count == 1

        # Second call hits cache, no extra Haiku call
        with patch.object(
            match_explainer, "call_haiku", AsyncMock(return_value=fake),
        ) as mock2:
            out2 = await match_explainer.explain_match(
                session_id="sess-1", job=_BASE_JOB,
                score_breakdown=_BREAKDOWN, barriers=["TRANSIT"],
                retrieved_docs=_DOCS,
            )
        assert out2["cached"] is True
        assert out2["text"] == fake.text
        assert mock2.call_count == 0


class TestExplainMatchFallback:
    @pytest.mark.asyncio
    async def test_haiku_error_falls_back_to_deterministic(self) -> None:
        """HaikuError is caught — caller gets deterministic text."""
        with patch.object(
            match_explainer, "call_haiku",
            AsyncMock(side_effect=HaikuError("api down")),
        ):
            out = await match_explainer.explain_match(
                session_id="sess-2", job=_BASE_JOB,
                score_breakdown=_BREAKDOWN, barriers=["CHILDCARE"],
                retrieved_docs=_DOCS,
            )
        assert out["source"] == "fallback"
        assert out["cached"] is False
        # Strongest signals from breakdown should appear
        assert "title_family" in out["text"] or "industry" in out["text"]
        # Cited resource should appear in fallback
        assert "Trinity Metro" in out["text"]

    @pytest.mark.asyncio
    async def test_fallback_with_no_docs_uses_wstc(self) -> None:
        """When no docs retrieved, fallback recommends WSTC."""
        with patch.object(
            match_explainer, "call_haiku",
            AsyncMock(side_effect=HaikuError("api down")),
        ):
            out = await match_explainer.explain_match(
                session_id="sess-3", job=_BASE_JOB,
                score_breakdown=_BREAKDOWN, barriers=[],
                retrieved_docs=[],
            )
        assert "Workforce Solutions" in out["text"]
        assert "1200 Circle Dr" in out["text"]

    @pytest.mark.asyncio
    async def test_fallback_with_low_breakdown_skips_factor_text(self) -> None:
        """All factors <0.30 -> generic factor_text, no false claims."""
        weak_breakdown = {
            "skills": 0.10, "title_family": 0.05, "industry": 0.0,
            "years": 0.0, "education": 0.0, "certifications": 0.0,
            "industry_aligned": False,
        }
        with patch.object(
            match_explainer, "call_haiku",
            AsyncMock(side_effect=HaikuError("down")),
        ):
            out = await match_explainer.explain_match(
                session_id="sess-4", job=_BASE_JOB,
                score_breakdown=weak_breakdown, barriers=[],
                retrieved_docs=_DOCS,
            )
        assert "matched this position based on your overall profile" in out["text"]
