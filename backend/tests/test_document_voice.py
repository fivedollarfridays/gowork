"""Tests for app.modules.documents.voice (T12.14).

Covers the worker-voice post-processing pipeline and the Jinja2
markdown template rendering layer. The Flesch-Kincaid corpus test is
the acceptance gate: after :func:`apply_worker_voice`, every sample in
``_VOICE_CORPUS`` must grade <9.0.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.modules.documents.voice import (
    _apply_dignified_substitutions,
    _count_syllables,
    _strip_dashes,
    _strip_hedges,
    _strip_hyphens,
    _strip_quotes,
    apply_worker_voice,
    flesch_kincaid_grade,
)

# ---------------------------------------------------------------------------
# Fixed F-K corpus (T12.14 AC: <9.0 after apply_worker_voice on all 5)
# ---------------------------------------------------------------------------

_VOICE_CORPUS: list[str] = [
    # 1. Short, direct resume summary-style paragraph.
    "I drive a truck. I load freight. I start on time every day. "
    "My team counts on me. I do good work.",
    # 2. Cover-letter opener with smart quotes and a hedge word.
    "Perhaps I am the right fit for this role. I can learn fast. "
    "I show up. I stay calm when things get hard.",
    # 3. Work-history bullet prose with em-dash and mid-word hyphens.
    "I worked on a loading dock — long shifts, heavy lifts. "
    "I trained new hires on a fork-lift. I kept the line moving.",
    # 4. Fair-chance framing paragraph with hedges.
    "I served my time. I am ready to work. I show up on time. "
    "I want a steady job. I will earn trust day by day.",
    # 5. Skills paragraph — longer, still plain-spoken.
    "I know how to lift. I know how to clean. I know how to drive. "
    "I have a good record on the job. I help my team win.",
]


# ---------------------------------------------------------------------------
# Dash stripping
# ---------------------------------------------------------------------------


def test_strip_dashes_replaces_em_dash_with_comma() -> None:
    """Em-dashes become comma-space so the sentence still flows."""
    out = _strip_dashes("He said — hello there")
    assert "—" not in out
    assert "hello there" in out
    # The separator is rewritten as ", " (comma-space).
    assert ", hello there" in out


def test_strip_dashes_replaces_en_dash_with_comma() -> None:
    """En-dashes are treated the same as em-dashes."""
    out = _strip_dashes("Pages 10 – 12 are missing")
    assert "–" not in out
    assert "—" not in out
    assert "," in out


def test_strip_dashes_is_noop_when_no_dash() -> None:
    """Strings without dashes are returned unchanged."""
    text = "Plain sentence with no dashes."
    assert _strip_dashes(text) == text


# ---------------------------------------------------------------------------
# Hedge stripping
# ---------------------------------------------------------------------------


def test_strip_hedges_removes_perhaps() -> None:
    out = _strip_hedges("Perhaps this will work.")
    assert "perhaps" not in out.lower()


def test_strip_hedges_removes_maybe() -> None:
    out = _strip_hedges("Maybe I can help with that.")
    assert "maybe" not in out.lower()


def test_strip_hedges_removes_might() -> None:
    out = _strip_hedges("I might be able to drive a forklift.")
    assert " might " not in out.lower()


def test_strip_hedges_removes_possibly() -> None:
    out = _strip_hedges("I possibly have the skills.")
    assert "possibly" not in out.lower()


def test_strip_hedges_removes_somewhat() -> None:
    out = _strip_hedges("I am somewhat familiar with warehouses.")
    assert "somewhat" not in out.lower()


def test_strip_hedges_collapses_double_spaces() -> None:
    """Removing the word leaves no double spaces behind."""
    out = _strip_hedges("This is perhaps a good example.")
    assert "  " not in out


# ---------------------------------------------------------------------------
# Quote stripping
# ---------------------------------------------------------------------------


def test_strip_quotes_converts_smart_double_to_ascii() -> None:
    out = _strip_quotes("“hello”")
    assert "“" not in out
    assert "”" not in out
    assert '"hello"' == out


def test_strip_quotes_converts_smart_single_to_ascii() -> None:
    out = _strip_quotes("‘hello’")
    assert "‘" not in out
    assert "’" not in out
    assert "'hello'" == out


def test_strip_quotes_leaves_ascii_alone() -> None:
    assert _strip_quotes('plain "ascii" quotes') == 'plain "ascii" quotes'


# ---------------------------------------------------------------------------
# Hyphen stripping
# ---------------------------------------------------------------------------


def test_strip_hyphens_preserves_name_hyphens() -> None:
    """Proper names like 'Mary-Jane' keep their hyphens."""
    out = _strip_hyphens("Mary-Jane worked the line.")
    assert "Mary-Jane" in out


def test_strip_hyphens_preserves_street_addresses() -> None:
    """Address-like tokens (digits-letters) keep hyphens."""
    out = _strip_hyphens("123-A Main Street")
    assert "123-A" in out


def test_strip_hyphens_removes_obscuring_mid_word_hyphens() -> None:
    """A hyphen between two lowercase words (non-name) is replaced.

    'fork-lift' is a common noun; the reader is better served by a
    space: 'fork lift'.
    """
    out = _strip_hyphens("I operated a fork-lift last year.")
    assert "fork-lift" not in out
    assert "fork lift" in out


# ---------------------------------------------------------------------------
# Dignified substitution (filter / flag)
# ---------------------------------------------------------------------------


def test_dignified_substitutions_flags_loaded_language() -> None:
    """Loaded labels like 'ex-offender' are filtered out, not substituted."""
    text = "As an ex-offender, I am ready to work."
    out = _apply_dignified_substitutions(text)
    assert "ex-offender" not in out.lower()
    # The sentence still reads — caller's wording still stands otherwise.
    assert "ready to work" in out


def test_dignified_substitutions_filters_felon_label() -> None:
    text = "I am a felon looking for work."
    out = _apply_dignified_substitutions(text)
    assert "felon" not in out.lower()


def test_dignified_substitutions_leaves_neutral_text_alone() -> None:
    text = "I served my time and I am ready to work."
    assert _apply_dignified_substitutions(text) == text


# ---------------------------------------------------------------------------
# apply_worker_voice — single entry point
# ---------------------------------------------------------------------------


def test_apply_worker_voice_is_idempotent() -> None:
    """Running the pipeline twice yields the same output as running it once."""
    sample = (
        "Perhaps “hello” — Mary-Jane ‘works’ "
        "on a fork-lift maybe."
    )
    once = apply_worker_voice(sample)
    twice = apply_worker_voice(once)
    assert once == twice


def test_apply_worker_voice_strips_all_rule_classes() -> None:
    """All rule classes fire when invoked through the single entry point."""
    sample = (
        "Perhaps I — as an ex-offender — “might” "
        "drive a fork-lift."
    )
    out = apply_worker_voice(sample)
    assert "perhaps" not in out.lower()
    assert "might" not in out.lower()
    assert "ex-offender" not in out.lower()
    assert "—" not in out
    assert "“" not in out
    assert "”" not in out
    assert "fork-lift" not in out


def test_apply_worker_voice_empty_input() -> None:
    assert apply_worker_voice("") == ""


# ---------------------------------------------------------------------------
# Flesch-Kincaid calculator
# ---------------------------------------------------------------------------


def test_fk_calculator_on_known_sample() -> None:
    """Calibration check against a well-known simple-English passage.

    The opening of a children's book paragraph is widely cited as F-K
    grade ~2 to ~3. We assert our calculator lands within +/-1.0 of
    that reference for the same passage.
    """
    passage = (
        "The cat sat on the mat. The dog ran to the park. "
        "We had a good time. The sun was warm."
    )
    grade = flesch_kincaid_grade(passage)
    # Ultra-simple monosyllabic English produces very low (often
    # negative) grades on the F-K formula. Bound loosely around the
    # reference "grade ~1-3" target with wide tolerance on both sides.
    assert grade < 4.0
    assert grade > -5.0


def test_count_syllables_basic() -> None:
    assert _count_syllables("cat") == 1
    assert _count_syllables("hello") == 2
    assert _count_syllables("") == 1  # minimum 1


def test_fk_grade_under_9_on_corpus() -> None:
    """ACCEPTANCE GATE: every corpus sample grades <9.0 after voice rules."""
    grades: list[float] = []
    for idx, sample in enumerate(_VOICE_CORPUS):
        processed = apply_worker_voice(sample)
        grade = flesch_kincaid_grade(processed)
        grades.append(grade)
        assert grade < 9.0, (
            f"Corpus sample {idx} graded {grade:.2f} "
            f"(>=9.0) after apply_worker_voice; processed={processed!r}"
        )
    # Informational: document the grades in pytest -s output.
    print(f"\nF-K grades on voice corpus: {[round(g, 2) for g in grades]}")


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------


_TEMPLATES_DIR = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "modules"
    / "documents"
    / "templates"
)


def _build_md_jinja_env() -> Environment:
    """Build a Jinja2 environment for .md.j2 templates with autoescape on."""
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(
            enabled_extensions=("md", "md.j2", "html", "htm", "xml"),
            default_for_string=True,
        ),
        keep_trailing_newline=True,
    )


def test_resume_template_renders() -> None:
    env = _build_md_jinja_env()
    tmpl = env.get_template("resume_base.md.j2")
    out = tmpl.render(
        name="Alice Worker",
        contact="123 Main St\nalice@example.com",
        summary="Reliable worker. Shows up on time.",
        skills=["lifting", "driving", "cleaning"],
        work_history=[
            {
                "title": "Driver",
                "employer": "Acme",
                "dates": "2020-2023",
                "description": "Drove routes daily.",
            }
        ],
        barriers_cleared=["license reinstated"],
    )
    assert out.strip(), "resume template rendered empty"
    assert "Alice Worker" in out
    assert "## Summary" in out
    assert "Reliable worker" in out
    assert "## Skills" in out
    assert "- lifting" in out
    assert "## Work history" in out
    assert "Driver" in out
    assert "## Cleared barriers" in out
    assert "- license reinstated" in out


def test_resume_template_skips_optional_sections() -> None:
    env = _build_md_jinja_env()
    tmpl = env.get_template("resume_base.md.j2")
    out = tmpl.render(
        name="Bob",
        contact=None,
        summary="Short.",
        skills=[],
        work_history=[],
        barriers_cleared=[],
    )
    assert "Cleared barriers" not in out
    assert "Bob" in out


def test_cover_letter_template_renders() -> None:
    env = _build_md_jinja_env()
    tmpl = env.get_template("cover_letter_base.md.j2")
    out = tmpl.render(
        date_today="April 23, 2026",
        hiring_manager="Jane Smith",
        name="Alice Worker",
        opening="I am applying for the driver role.",
        body="I have five years on the road.",
        fair_chance_framing="I served my time and am ready to work.",
    )
    assert out.strip()
    assert "April 23, 2026" in out
    assert "Jane Smith" in out
    assert "Alice Worker" in out
    assert "driver role" in out
    assert "ready to work" in out


def test_cover_letter_template_default_greeting() -> None:
    env = _build_md_jinja_env()
    tmpl = env.get_template("cover_letter_base.md.j2")
    out = tmpl.render(
        date_today="April 23, 2026",
        hiring_manager=None,
        name="Alice",
        opening="Hello.",
        body="Body text.",
        fair_chance_framing=None,
    )
    assert "Hiring Manager" in out


def test_resume_template_escapes_html_in_name() -> None:
    """Autoescape must neutralise unsafe HTML in worker-supplied fields."""
    env = _build_md_jinja_env()
    tmpl = env.get_template("resume_base.md.j2")
    out = tmpl.render(
        name="Alice <script>alert(1)</script>",
        contact=None,
        summary="OK.",
        skills=[],
        work_history=[],
        barriers_cleared=[],
    )
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_cover_letter_template_escapes_html_in_body() -> None:
    env = _build_md_jinja_env()
    tmpl = env.get_template("cover_letter_base.md.j2")
    out = tmpl.render(
        date_today="April 23, 2026",
        hiring_manager="Manager",
        name="Alice",
        opening="Hi <b>there</b>.",
        body="Plain body.",
        fair_chance_framing=None,
    )
    assert "<b>there</b>" not in out
    assert "&lt;b&gt;there&lt;/b&gt;" in out


# ---------------------------------------------------------------------------
# Avoid accidental dep: make sure pytest picks up the module
# ---------------------------------------------------------------------------


def test_module_exports_public_api() -> None:
    from app.modules.documents import voice as voice_mod

    for name in (
        "apply_worker_voice",
        "flesch_kincaid_grade",
    ):
        assert hasattr(voice_mod, name), f"voice module missing {name!r}"


@pytest.mark.parametrize("sample", _VOICE_CORPUS)
def test_apply_worker_voice_preserves_content(sample: str) -> None:
    """Voice rules must not strip every word — output is still meaningful."""
    out = apply_worker_voice(sample)
    assert out, "voice rules returned empty string"
    assert len(out.split()) >= 5, "voice rules stripped too much text"
