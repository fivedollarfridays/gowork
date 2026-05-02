"""Tests for the demo persona loader."""

from __future__ import annotations

import pytest

from app.demo.persona_loader import (
    PersonaNotFound,
    get_persona,
    list_persona_ids,
    load_all_personas,
)


class TestLoadAllPersonas:
    def test_loads_five_canonical_personas(self) -> None:
        """All 5 demo personas (carlos, nurse, forklift, welder, csr) loadable."""
        personas = load_all_personas()
        expected = {"carlos", "nurse", "forklift", "welder", "csr"}
        assert expected.issubset(set(personas.keys())), (
            f"Missing personas: {expected - set(personas.keys())}"
        )

    def test_each_persona_has_required_fields(self) -> None:
        """Every persona JSON has id, summary, city, primary_barriers, etc."""
        personas = load_all_personas()
        required = {
            "id", "display_name", "city", "summary", "zip_code",
            "primary_barriers", "barrier_severity",
        }
        for pid, data in personas.items():
            assert required.issubset(set(data.keys())), (
                f"Persona {pid} missing fields"
            )

    def test_each_persona_is_fort_worth(self) -> None:
        """All canonical personas are Fort Worth residents."""
        personas = load_all_personas()
        for pid, data in personas.items():
            assert data["city"] == "fort-worth", f"{pid} is not fort-worth"

    def test_each_persona_has_resume_text(self) -> None:
        """Resume text is present and non-trivial (>50 chars)."""
        personas = load_all_personas()
        for pid, data in personas.items():
            resume = data.get("resume_text", "")
            assert len(resume) > 50, f"Persona {pid} resume too short"


class TestGetPersona:
    def test_carlos_loadable(self) -> None:
        carlos = get_persona("carlos")
        assert carlos["id"] == "carlos"
        assert "criminal_record" in carlos["primary_barriers"]

    def test_nurse_loadable(self) -> None:
        nurse = get_persona("nurse")
        assert nurse["id"] == "nurse"
        assert "RN" in nurse["certifications"]

    def test_unknown_persona_raises(self) -> None:
        with pytest.raises(PersonaNotFound):
            get_persona("unknown-persona-xyz")


class TestListPersonaIds:
    def test_returns_sorted_ids(self) -> None:
        ids = list_persona_ids()
        assert ids == sorted(ids)
        assert "carlos" in ids
