"""Tests for two-stage Spanish resume polish."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.integrations.llm import _cache, spanish_polish
from app.integrations.llm._haiku_client import HaikuError, HaikuResult


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    _cache.spanish_polish_cache.clear()


_CNA_RESUME = (
    "Soy enfermera certificada con cinco años de experiencia en hospitales "
    "de Texas. Mis responsabilidades incluyen el cuidado de pacientes y "
    "documentación. Tengo licencia de CNA del estado de Texas."
)
_FORKLIFT_RESUME = (
    "Operador de montacargas con tres años de experiencia en almacén. "
    "Trabajé en bodega de embalaje y envío."
)
_ENGLISH_RESUME = (
    "Certified nursing assistant with five years of experience in Texas "
    "hospitals. My responsibilities include patient care and documentation."
)


class TestDetectSpanish:
    def test_spanish_text_detected(self) -> None:
        assert spanish_polish._detect_spanish(_CNA_RESUME) is True

    def test_english_text_not_detected(self) -> None:
        assert spanish_polish._detect_spanish(_ENGLISH_RESUME) is False

    def test_short_text_not_detected(self) -> None:
        assert spanish_polish._detect_spanish("Hola mundo.") is False


class TestDictTranslate:
    def test_cna_phrases_translated(self) -> None:
        translated, _ = spanish_polish._dict_translate(_CNA_RESUME)
        # "enfermera" -> "nurse", "experiencia" -> "experience"
        assert "nurse" in translated.lower()
        assert "experience" in translated.lower()

    def test_forklift_phrases_translated(self) -> None:
        translated, _ = spanish_polish._dict_translate(_FORKLIFT_RESUME)
        assert "forklift" in translated.lower()
        assert "warehouse" in translated.lower()
        assert "shipping" in translated.lower()

    def test_residual_finds_remaining_spanish_chars(self) -> None:
        text = "Working with máquinas industriales desconocidas."
        _, residual = spanish_polish._dict_translate(text)
        assert "máquinas" in residual or "máquina" in residual.__str__()


class TestPolishSpanishResume:
    @pytest.mark.asyncio
    async def test_english_input_passthrough(self) -> None:
        out = await spanish_polish.polish_spanish_resume(_ENGLISH_RESUME)
        assert out["stage"] == "passthrough"
        assert out["english_text"] == _ENGLISH_RESUME

    @pytest.mark.asyncio
    async def test_low_residual_uses_dict_only(self) -> None:
        """CNA resume's vocabulary is in our dict -> stage=='dict', no Haiku."""
        with patch.object(
            spanish_polish, "call_haiku",
            AsyncMock(side_effect=AssertionError("should not call")),
        ):
            out = await spanish_polish.polish_spanish_resume(_CNA_RESUME)
        assert out["stage"] == "dict"
        assert "nurse" in out["english_text"].lower()

    @pytest.mark.asyncio
    async def test_high_residual_invokes_haiku(self) -> None:
        """Resume full of unknown Spanish -> Haiku polishes the residual."""
        weird_resume = (
            "Trabajé como técnico en máquinas hidráulicas y vehículos "
            "diésel. Conocimientos en sistemas neumáticos y rodamientos."
        )
        fake = HaikuResult(
            text="Worked as a hydraulic technician and diesel vehicle mechanic. "
                 "Knowledge of pneumatic systems and bearings.",
            input_tokens=600, output_tokens=80,
        )
        with patch.object(
            spanish_polish, "call_haiku", AsyncMock(return_value=fake),
        ):
            out = await spanish_polish.polish_spanish_resume(weird_resume)
        assert out["stage"] == "haiku"
        assert "hydraulic" in out["english_text"].lower()

    @pytest.mark.asyncio
    async def test_haiku_failure_falls_back_to_dict(self) -> None:
        """If Haiku errors, we still return the dict-translated text."""
        weird_resume = (
            "Trabajé como técnico en máquinas hidráulicas y vehículos "
            "diésel. Conocimientos en sistemas neumáticos y rodamientos."
        )
        with patch.object(
            spanish_polish, "call_haiku",
            AsyncMock(side_effect=HaikuError("api down")),
        ):
            out = await spanish_polish.polish_spanish_resume(weird_resume)
        assert out["stage"] == "dict"

    @pytest.mark.asyncio
    async def test_cache_hit_skips_translation(self) -> None:
        out1 = await spanish_polish.polish_spanish_resume(_CNA_RESUME)
        out2 = await spanish_polish.polish_spanish_resume(_CNA_RESUME)
        assert out1["cached"] is False
        assert out2["cached"] is True
        assert out2["english_text"] == out1["english_text"]

    @pytest.mark.asyncio
    async def test_empty_input_passthrough(self) -> None:
        out = await spanish_polish.polish_spanish_resume("")
        assert out["stage"] == "passthrough"
        assert out["english_text"] == ""
