"""Tests for the Haiku-augmented job description summarizer."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.integrations.llm import _cache, summarizer
from app.integrations.llm._haiku_client import HaikuError, HaikuResult


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    _cache.job_summary_cache.clear()


_LONG_DESC = (
    "We are seeking a Certified Nursing Assistant to join our Fort Worth "
    "team. Responsibilities include patient care, vital signs monitoring, "
    "documentation, and assisting with daily living activities. Must have "
    "current Texas CNA license and at least one year of experience in a "
    "long-term care or hospital setting. We offer competitive wages, "
    "health insurance, and paid time off. Background check required."
)


class TestSummarizeJobHaikuPath:
    @pytest.mark.asyncio
    async def test_valid_json_response_parsed_and_cached(self) -> None:
        """Haiku returns structured JSON -> we parse and cache it."""
        haiku_payload = {
            "pitch": "Hospital CNA role in Fort Worth focused on direct patient care. "
                     "Texas CNA license required, one year experience preferred.",
            "duties": [
                "Monitor patient vital signs",
                "Document care notes",
                "Assist with daily living activities",
            ],
        }
        fake = HaikuResult(
            text=json.dumps(haiku_payload), input_tokens=400, output_tokens=80,
        )
        with patch.object(
            summarizer, "call_haiku", AsyncMock(return_value=fake),
        ) as mock_call:
            out = await summarizer.summarize_job(
                title="CNA", description=_LONG_DESC,
            )
        assert out["source"] == "haiku"
        assert out["cached"] is False
        assert "patient care" in out["pitch"]
        assert len(out["duties"]) == 3

        # Second call hits cache
        with patch.object(
            summarizer, "call_haiku", AsyncMock(return_value=fake),
        ) as mock2:
            out2 = await summarizer.summarize_job(
                title="CNA", description=_LONG_DESC,
            )
        assert mock_call.call_count == 1
        assert mock2.call_count == 0
        assert out2["cached"] is True

    @pytest.mark.asyncio
    async def test_json_with_code_fences_still_parses(self) -> None:
        """If Haiku wraps JSON in ```json fences, we strip them."""
        payload = {"pitch": "Fort Worth role.", "duties": ["Do A", "Do B"]}
        wrapped = f"```json\n{json.dumps(payload)}\n```"
        fake = HaikuResult(text=wrapped, input_tokens=300, output_tokens=50)
        with patch.object(
            summarizer, "call_haiku", AsyncMock(return_value=fake),
        ):
            out = await summarizer.summarize_job(
                title="CNA", description=_LONG_DESC,
            )
        assert out["source"] == "haiku"
        assert out["pitch"] == "Fort Worth role."


class TestSummarizeJobFallback:
    @pytest.mark.asyncio
    async def test_haiku_error_falls_back(self) -> None:
        with patch.object(
            summarizer, "call_haiku",
            AsyncMock(side_effect=HaikuError("api down")),
        ):
            out = await summarizer.summarize_job(
                title="CNA", description=_LONG_DESC,
            )
        assert out["source"] == "fallback"
        assert "Certified Nursing Assistant" in out["pitch"]

    @pytest.mark.asyncio
    async def test_invalid_json_falls_back(self) -> None:
        """Haiku returns non-JSON gibberish -> fallback."""
        fake = HaikuResult(
            text="Sorry, I can't help with that.",
            input_tokens=200, output_tokens=20,
        )
        with patch.object(
            summarizer, "call_haiku", AsyncMock(return_value=fake),
        ):
            out = await summarizer.summarize_job(
                title="CNA", description=_LONG_DESC,
            )
        assert out["source"] == "fallback"

    @pytest.mark.asyncio
    async def test_short_description_skips_haiku(self) -> None:
        """<30 char description -> fallback without invoking Haiku."""
        with patch.object(
            summarizer, "call_haiku",
            AsyncMock(side_effect=AssertionError("should not call")),
        ):
            out = await summarizer.summarize_job(
                title="CNA", description="Short job",
            )
        assert out["source"] == "fallback"

    @pytest.mark.asyncio
    async def test_pitch_too_short_falls_back(self) -> None:
        """Haiku returns valid JSON but pitch <10 chars -> fallback."""
        fake = HaikuResult(
            text=json.dumps({"pitch": "Hi.", "duties": []}),
            input_tokens=200, output_tokens=20,
        )
        with patch.object(
            summarizer, "call_haiku", AsyncMock(return_value=fake),
        ):
            out = await summarizer.summarize_job(
                title="CNA", description=_LONG_DESC,
            )
        assert out["source"] == "fallback"


class TestDescriptionHash:
    def test_same_text_yields_same_hash(self) -> None:
        a = summarizer._description_hash("hello world description")
        b = summarizer._description_hash("hello world description")
        assert a == b

    def test_different_text_yields_different_hash(self) -> None:
        a = summarizer._description_hash("description A")
        b = summarizer._description_hash("description B")
        assert a != b
