"""Tests for the Haiku-augmented Monday-morning next-step composer."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.integrations.llm import _cache, next_step_composer
from app.integrations.llm._haiku_client import HaikuError, HaikuResult


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    _cache.next_step_cache.clear()


_BARRIERS = ["TRANSIT", "CHILDCARE"]
_DETERMINISTIC = [
    "Visit Workforce Solutions for Tarrant County at 1200 Circle Dr",
    "Contact Trinity Metro for transit support",
    "Call Tarrant Area Food Bank for emergency food",
]
_DOCS = [
    {"title": "Trinity Metro CNA Bus Pass Program",
     "text": "Discounted bus passes for healthcare commutes."},
    {"title": "Workforce Solutions for Tarrant County",
     "text": "WSTC offers direct intros at 1200 Circle Dr."},
]


class TestComposeNextStepsHaikuPath:
    @pytest.mark.asyncio
    async def test_grounded_haiku_response_returned(self) -> None:
        """Well-formed grounded Haiku output passes through and is cached."""
        haiku_text = (
            "Call Trinity Metro at 817-215-8600 to apply for a bus pass.\n"
            "Visit Workforce Solutions for Tarrant County at 1200 Circle Dr.\n"
            "Reach out to Tarrant Area Food Bank for emergency support.\n"
            "Schedule a childcare consult Monday afternoon."
        )
        fake = HaikuResult(text=haiku_text, input_tokens=400, output_tokens=120)
        with patch.object(
            next_step_composer, "call_haiku", AsyncMock(return_value=fake),
        ):
            out = await next_step_composer.compose_next_steps(
                session_id="sess-A", barriers=_BARRIERS,
                deterministic_steps=_DETERMINISTIC, retrieved_docs=_DOCS,
            )
        assert out["source"] == "haiku"
        assert out["cached"] is False
        assert len(out["steps"]) == 4
        assert any("Trinity" in s for s in out["steps"])

    @pytest.mark.asyncio
    async def test_cache_hit_skips_haiku(self) -> None:
        """Second call within TTL returns cached steps, no Haiku invocation."""
        haiku_text = (
            "Visit Workforce Solutions Monday morning.\n"
            "Contact Trinity Metro for transit help.\n"
            "Reach out to Tarrant Area Food Bank.\n"
            "Schedule childcare consult."
        )
        fake = HaikuResult(text=haiku_text, input_tokens=400, output_tokens=120)
        with patch.object(
            next_step_composer, "call_haiku", AsyncMock(return_value=fake),
        ) as mock1:
            out1 = await next_step_composer.compose_next_steps(
                session_id="sess-cache", barriers=_BARRIERS,
                deterministic_steps=_DETERMINISTIC, retrieved_docs=_DOCS,
            )
        with patch.object(
            next_step_composer, "call_haiku", AsyncMock(return_value=fake),
        ) as mock2:
            out2 = await next_step_composer.compose_next_steps(
                session_id="sess-cache", barriers=_BARRIERS,
                deterministic_steps=_DETERMINISTIC, retrieved_docs=_DOCS,
            )
        assert mock1.call_count == 1
        assert mock2.call_count == 0
        assert out2["cached"] is True
        assert out2["steps"] == out1["steps"]


class TestComposeNextStepsFallback:
    @pytest.mark.asyncio
    async def test_haiku_error_returns_deterministic(self) -> None:
        """HaikuError -> deterministic steps."""
        with patch.object(
            next_step_composer, "call_haiku",
            AsyncMock(side_effect=HaikuError("api down")),
        ):
            out = await next_step_composer.compose_next_steps(
                session_id="sess-X", barriers=_BARRIERS,
                deterministic_steps=_DETERMINISTIC, retrieved_docs=_DOCS,
            )
        assert out["source"] == "fallback"
        assert out["steps"] == _DETERMINISTIC

    @pytest.mark.asyncio
    async def test_ungrounded_output_rejected(self) -> None:
        """If Haiku invents resources we never gave it, fall back."""
        bad_text = (
            "Apply for a job at FakeCorp Industries.\n"
            "Call MadeUpProgram now.\n"
            "Visit Imaginary Resource Center.\n"
            "Email NotARealAgency."
        )
        fake = HaikuResult(text=bad_text, input_tokens=300, output_tokens=80)
        with patch.object(
            next_step_composer, "call_haiku", AsyncMock(return_value=fake),
        ):
            out = await next_step_composer.compose_next_steps(
                session_id="sess-bad", barriers=_BARRIERS,
                deterministic_steps=_DETERMINISTIC, retrieved_docs=_DOCS,
            )
        assert out["source"] == "fallback"
        assert out["steps"] == _DETERMINISTIC

    @pytest.mark.asyncio
    async def test_too_few_steps_rejected(self) -> None:
        """If Haiku returns 1 step, reject and fall back."""
        fake = HaikuResult(
            text="Only one step.", input_tokens=100, output_tokens=10,
        )
        with patch.object(
            next_step_composer, "call_haiku", AsyncMock(return_value=fake),
        ):
            out = await next_step_composer.compose_next_steps(
                session_id="sess-thin", barriers=_BARRIERS,
                deterministic_steps=_DETERMINISTIC, retrieved_docs=_DOCS,
            )
        assert out["source"] == "fallback"


class TestParseSteps:
    def test_strips_numbering_and_bullets(self) -> None:
        """Numbers, dots, and bullets are scrubbed from each step."""
        text = (
            "1. Visit Workforce Solutions for Tarrant County\n"
            "- Contact Trinity Metro about a bus pass\n"
            "* Call Tarrant Area Food Bank to schedule support\n"
            "4) Reach out to childcare resource center"
        )
        steps = next_step_composer._parse_steps(text)
        assert len(steps) == 4
        for s in steps:
            assert not s.startswith(("-", "*", "1", "4"))

    def test_drops_empty_and_too_short_lines(self) -> None:
        text = "OK\n\nVisit Workforce Solutions for Tarrant County today\nx"
        steps = next_step_composer._parse_steps(text)
        assert len(steps) == 1
