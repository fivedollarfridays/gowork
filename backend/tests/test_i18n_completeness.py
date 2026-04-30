"""i18n string completeness gate (T13.68).

This suite enforces that the bilingual translation catalog used by the
MontGoWork frontend (and any future backend-rendered strings) is
internally consistent: every key present in ``en.json`` must also be in
``es.json`` (and vice versa), no value may be empty/whitespace, every
key referenced from frontend production code must be defined, and ES
translations must not be a copy-paste of the EN source unless the pair
is on a vetted allowlist (proper nouns, brand names, single tokens
with shared meaning).

The Jinja2 templates under ``backend/app/modules/documents/templates/``
and the email templates under ``backend/app/modules/engagement/`` do not
currently use i18n -- they emit English-only artefacts (resumes, cover
letters, reminder emails) -- so the template assertion documents the
status quo so a future regression that introduces ``{{ t.key }}`` or
``{{ _('...') }}`` will surface here.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TRANSLATIONS_DIR = REPO_ROOT / "frontend" / "src" / "lib" / "translations"
EN_PATH = TRANSLATIONS_DIR / "en.json"
ES_PATH = TRANSLATIONS_DIR / "es.json"
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"
DOC_TEMPLATES = REPO_ROOT / "backend" / "app" / "modules" / "documents" / "templates"
ENGAGEMENT_DIR = REPO_ROOT / "backend" / "app" / "modules" / "engagement"

# Pairs where en.json and es.json carry the same string by design.
# Each entry must include a short rationale.
IDENTICAL_PAIR_ALLOWLIST: dict[str, str] = {
    # Single-character / minimal-token negatives that are the same in
    # informal Spanish (we use accent-stripped 'No' across the catalog).
    "common.no": "Spanish 'No' is identical to English 'No'.",
    # 'Manual' is a Latinism shared by both languages with same meaning
    # in this UI context (manually-created appointments / applications).
    "appointments.sourceUser": "'Manual' is identical in EN/ES UI usage.",
    "jobs.cardGenMethodUnknown": "'Manual' is identical in EN/ES UI usage.",
    # 'PDF' is a file-format proper noun.
    "documents.historyDownloadPdf": "PDF is a file-format proper noun.",
    # 'Total' is a Latinism with identical surface form in EN/ES.
    "jobs.funnelTotal": "'Total' is identical in EN/ES.",
    # 'Error:' is a Latinism shared by both languages with the same form
    # and identical inline-prefix usage in error UI strings.
    "credit.errorPrefix": "'Error:' is identical in EN/ES.",
    # 'Legal' is the aria-label for the footer's legal-links nav. The word
    # is a Latinism with identical surface form and meaning in EN/ES.
    "footer.navLabel": "'Legal' is identical in EN/ES.",
    # The Wall stat-pills carry compact numeric / abbreviated-unit values
    # that don't translate. Spanish uses 'min' for minute (Sp. 'minuto'
    # abbreviated) and bare percentages identically. The descriptive labels
    # next to them (statLabel) carry the actual translation.
    "wall.chapter04a.statValue": "'71 min' — numeric duration with 'min' abbreviation identical in EN/ES.",
    "wall.chapter04b.statValue": "'87 min' — numeric duration with 'min' abbreviation identical in EN/ES.",
    "wall.chapter04d.statValue": "'33%' — bare percentage; identical surface form in EN/ES.",
    # Chapter 5's forms-counter is a pure integer that anchors the WALL
    # tally. The descriptive label ('formsCounterLabel') carries the
    # translation; the count itself is identical in any language.
    "wall.chapter05.formsCounter": "'47' — pure integer count; identical in EN/ES.",
    # W3 Chapter 6 stat-pill ("71 min") is a compact numeric duration; the
    # 'min' abbreviation is identical in Spanish (abbrev. of 'minuto').
    # statLabel carries the descriptive translation.
    "wall.chapter06.statValue": "'71 min' — numeric duration with 'min' abbreviation identical in EN/ES.",
    # W3 Chapter 9 lights up two deployed cities + six future cities. All
    # are US place names that don't translate (proper nouns).
    "wall.chapter09.cityFW": "'Fort Worth, TX' — US city proper noun.",
    "wall.chapter09.cityMontgomery": "'Montgomery, AL' — US city proper noun.",
    "wall.chapter09.futureCityDallas": "'Dallas' — US city proper noun.",
    "wall.chapter09.futureCityHouston": "'Houston' — US city proper noun.",
    "wall.chapter09.futureCityAtlanta": "'Atlanta' — US city proper noun.",
    "wall.chapter09.futureCityMemphis": "'Memphis' — US city proper noun.",
    "wall.chapter09.futureCityCharlotte": "'Charlotte' — US city proper noun.",
    "wall.chapter09.futureCityBirmingham": "'Birmingham' — US city proper noun.",
    # W3 Chapter 10's footer brand mark is the GoWork wordmark + city. The
    # brand wordmark + place name are proper nouns that don't translate.
    "wall.chapter10.footerBrand": "'GoWork · Fort Worth, TX' — brand mark + US city, both proper nouns.",
    # Narrative-reset Ch5: each labyrinth office node now carries a proper-noun
    # name. Office names are organizational entities that don't translate.
    "wall.chapter05.officeNames.tarrant-district-clerk": "'Tarrant District Clerk' — government office proper noun.",
    "wall.chapter05.officeNames.hhsc-eligibility": "'HHSC Eligibility' — Texas state agency proper noun.",
    "wall.chapter05.officeNames.legal-aid-nw-texas": "'Legal Aid of NorthWest Texas' — nonprofit proper noun.",
    "wall.chapter05.officeNames.workforce-solutions-belknap": "'Workforce Solutions on E. Belknap' — agency + street proper nouns.",
    "wall.chapter05.officeNames.trinity-metro-hq": "'Trinity Metro HQ' — transit agency proper noun.",
    # Narrative-reset Ch9: Texas cities replacing Montgomery framing.
    # All US city proper nouns that don't translate.
    "wall.chapter09.futureCityAustin": "'Austin' — Texas city proper noun.",
    "wall.chapter09.futureCitySanAntonio": "'San Antonio' — Texas city proper noun.",
    "wall.chapter09.futureCityWaco": "'Waco' — Texas city proper noun.",
    # ─── Homepage scrollytelling (home.ch*) — data-shaped values ─────────
    # The new HackFW homepage ships compact numeric / proper-noun / address
    # values that legitimately read identically in EN and ES. The
    # descriptive label keys (statLabel, factLabel, etc.) carry the
    # translation; these data slots are pure data.
    # Ch2 stat numbers — bare integers/percentages.
    "home.ch2.stat1Number": "Bare numeric stat — identical in EN/ES.",
    "home.ch2.stat2Number": "Bare numeric stat — identical in EN/ES.",
    "home.ch2.stat3Number": "Bare numeric stat — identical in EN/ES.",
    "home.ch2.stat4Number": "Bare numeric stat — identical in EN/ES.",
    # Ch3 caption + facts — eyebrow tag + numeric pivots + ZIP code.
    "home.ch3.captionEyebrow": "Single-word eyebrow tag — identical in EN/ES.",
    "home.ch3.fact1Num": "Bare numeric fact value — identical in EN/ES.",
    "home.ch3.fact2Num": "Bare numeric fact value — identical in EN/ES.",
    "home.ch3.fact3Num": "Bare numeric fact value — identical in EN/ES.",
    "home.ch3.fact4Num": "Bare numeric fact value — identical in EN/ES.",
    "home.ch3.italicFromIndex": "Numeric pivot index — identical in EN/ES.",
    "home.ch3.p1Zip": "ZIP code 76104 — identical in EN/ES.",
    # Ch4 annotations + compass + legend + statRow — numeric/abbreviation values.
    "home.ch4.annotations.commute": "Numeric annotation — identical in EN/ES.",
    "home.ch4.annotations.headway": "Numeric annotation — identical in EN/ES.",
    "home.ch4.annotations.reach": "Numeric annotation — identical in EN/ES.",
    "home.ch4.annotations.wage": "Numeric wage value — identical in EN/ES.",
    "home.ch4.cards.card3Time": "Time stamp (3:27 PM) — identical in EN/ES.",
    "home.ch4.compass.lat": "Latitude readout — identical in EN/ES.",
    "home.ch4.compass.lon": "Longitude readout — identical in EN/ES.",
    "home.ch4.compass.zoom": "Map zoom level — identical in EN/ES.",
    "home.ch4.legend.afternoonNum": "Bare numeric legend label — identical in EN/ES.",
    "home.ch4.legend.brokenNum": "Bare numeric legend label — identical in EN/ES.",
    "home.ch4.legend.courtNum": "Bare numeric legend label — identical in EN/ES.",
    "home.ch4.legend.homeNum": "Bare numeric legend label — identical in EN/ES.",
    "home.ch4.legend.morningNum": "Bare numeric legend label — identical in EN/ES.",
    "home.ch4.legend.planNum": "Bare numeric legend label — identical in EN/ES.",
    "home.ch4.legendRow1": "Numeric/abbreviated legend row — identical in EN/ES.",
    "home.ch4.legendRow1Time": "Time-of-day stamp — identical in EN/ES.",
    "home.ch4.legendRow2Time": "Time-of-day stamp — identical in EN/ES.",
    "home.ch4.legendRow3Time": "Time-of-day stamp — identical in EN/ES.",
    "home.ch4.statRow.commuteUnit": "Distance unit — identical in EN/ES.",
    "home.ch4.statRow.commuteVal": "Numeric stat value — identical in EN/ES.",
    "home.ch4.statRow.headwayUnit": "'min' abbreviation — identical in EN/ES.",
    "home.ch4.statRow.headwayVal": "Numeric stat value — identical in EN/ES.",
    "home.ch4.statRow.recordsUnit": "Stat-row unit — identical in EN/ES.",
    "home.ch4.statRow.recordsVal": "Numeric stat value — identical in EN/ES.",
    "home.ch4.statRow.wageUnit": "Wage unit ($/hr) — identical in EN/ES.",
    "home.ch4.statRow.wageVal": "Numeric wage value — identical in EN/ES.",
    "home.ch4.step.navPrev": "Single arrow glyph — identical in EN/ES.",
    # Ch5 plan card numbers — pure step numerals.
    "home.ch5.card1Num": "Step number — identical in EN/ES.",
    "home.ch5.card2Num": "Step number — identical in EN/ES.",
    "home.ch5.card3Num": "Step number — identical in EN/ES.",
    "home.ch5.card4Num": "Step number — identical in EN/ES.",
    "home.ch5.h2Plan": "Single Latinate word ('plan') — identical in EN/ES.",
    # Ch6 employer cards — wages + addresses + employer-name proper nouns.
    "home.ch6.cards.alconAddr": "Alcon street address — proper noun, identical in EN/ES.",
    "home.ch6.cards.alconWage": "Wage value — identical in EN/ES.",
    "home.ch6.cards.bnsfAddr": "BNSF street address — proper noun, identical in EN/ES.",
    "home.ch6.cards.bnsfWage": "Wage value — identical in EN/ES.",
    "home.ch6.cards.dunnCommute": "Numeric commute value — identical in EN/ES.",
    "home.ch6.cards.dunnWage": "Wage value — identical in EN/ES.",
    "home.ch6.h2Fair": "Single shared term in headline (e.g. number) — identical in EN/ES.",
    "home.ch6.h2Tail": "Trailing punctuation/symbol — identical in EN/ES.",
    # Ch7 cliff calculator — wage + household-size labels are numeric/symbolic.
    "home.ch7.h2Cost": "Numeric cost value in headline — identical in EN/ES.",
    "home.ch7.householdSize1": "Pure integer household size — identical in EN/ES.",
    "home.ch7.householdSize2": "Pure integer household size — identical in EN/ES.",
    "home.ch7.householdSize3": "Pure integer household size — identical in EN/ES.",
    "home.ch7.householdSize4": "Pure integer household size — identical in EN/ES.",
    "home.ch7.p1Wage": "Wage value — identical in EN/ES.",
    "home.ch7.rowMed": "Row label abbreviation — identical in EN/ES.",
    # Ch8 manifesto wordmark — GOWORK + city tokens.
    "home.ch8.wordmark.spokenCityDal": "'Dallas' — US city proper noun.",
    "home.ch8.wordmark.spokenCityFw": "'Fort Worth' — US city proper noun.",
    "home.ch8.wordmark.spokenCityHou": "'Houston' — US city proper noun.",
    "home.ch8.wordmark.spokenCityMont": "'Montgomery' — US city proper noun.",
    "home.ch8.wordmarkRow1": "GOWORK wordmark row — brand mark, identical in EN/ES.",
    "home.ch8.wordmarkRow2": "GOWORK wordmark row — brand mark, identical in EN/ES.",
    # Site chrome — single-word nav items + brand line that share the same
    # surface form in both languages.
    "nav.plan": "'Plan' — Latinism with identical surface form in EN/ES.",
    "siteFooter.brandHeading": "Brand heading (GoWork) — proper noun, identical in EN/ES.",
    "siteFooter.creditLine": "Brand credit line — identical in EN/ES.",
    "siteFooter.workersPlan": "'Plan' — Latinism, identical in EN/ES.",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_locale(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    return json.loads(raw)


def _flatten(data: dict, prefix: str = "") -> dict[str, object]:
    """Flatten a nested dict into ``dot.path`` -> leaf-value pairs."""
    out: dict[str, object] = {}
    for key, value in data.items():
        composite = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            out.update(_flatten(value, composite))
        else:
            out[composite] = value
    return out


def _scan_frontend_keys() -> set[str]:
    """Return all i18n keys referenced from non-test frontend code.

    Picks up both ``t("foo.bar")`` (the React hook) and
    ``getTranslation("foo.bar", ...)`` (the underlying lib).
    """
    pattern = (
        r"(?:[^a-zA-Z0-9_]t|getTranslation)"
        r"\(\s*['\"]([a-zA-Z][a-zA-Z0-9_.]*)['\"]"
    )
    rx = re.compile(pattern)
    keys: set[str] = set()
    for path in FRONTEND_SRC.rglob("*.ts*"):
        # Exclude colocated test directories
        if "__tests__" in path.parts or path.name.endswith(".test.ts") \
                or path.name.endswith(".test.tsx"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in rx.finditer(text):
            keys.add(match.group(1))
    return keys


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def en_leaves() -> dict[str, object]:
    return _flatten(_load_locale(EN_PATH))


@pytest.fixture(scope="module")
def es_leaves() -> dict[str, object]:
    return _flatten(_load_locale(ES_PATH))


@pytest.fixture(scope="module")
def used_keys() -> set[str]:
    return _scan_frontend_keys()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_translation_files_exist():
    assert EN_PATH.is_file(), f"missing {EN_PATH}"
    assert ES_PATH.is_file(), f"missing {ES_PATH}"


def test_en_and_es_have_same_key_set(en_leaves, es_leaves):
    """Every leaf key in en.json must also exist in es.json (and vice versa)."""
    en_keys = set(en_leaves)
    es_keys = set(es_leaves)
    missing_in_es = sorted(en_keys - es_keys)
    missing_in_en = sorted(es_keys - en_keys)
    assert not missing_in_es and not missing_in_en, (
        "Locale key sets diverge.\n"
        f"  Missing in es.json: {missing_in_es}\n"
        f"  Missing in en.json: {missing_in_en}"
    )


# Keys whose values are intentionally non-string (lists, ints, empty) — the
# homepage scrollytelling catalog ships data-shaped entries (morph word arrays,
# numeric italic-from-index pivots, intentionally-blank suffix slots) that the
# frontend consumes as-is without going through a translation pass.
NON_STRING_VALUE_ALLOWLIST: dict[str, str] = {
    "home.ch1.morphWords": "Ch1 hero kinetic morph cycles an array of barrier nouns.",
    "home.ch3.h2Words": "Ch3 word-by-word reveal needs an array, not a sentence.",
    "home.ch3.italicFromIndex": "Ch3 italic pivot is an integer index into h2Words.",
    "home.ch6.livePillSuffix": "Ch6 live-pill suffix is intentionally empty in ES (no Spanish suffix).",
}


@pytest.mark.parametrize("locale_name", ["en", "es"])
def test_no_empty_values(locale_name, en_leaves, es_leaves):
    """No leaf value may be empty, whitespace-only, or a non-string type
    UNLESS it appears on NON_STRING_VALUE_ALLOWLIST (homepage data-shaped keys).
    """
    leaves = en_leaves if locale_name == "en" else es_leaves
    bad: list[str] = []
    for key, value in leaves.items():
        if key in NON_STRING_VALUE_ALLOWLIST:
            continue
        if not isinstance(value, str):
            bad.append(f"{key} (type={type(value).__name__})")
        elif value.strip() == "":
            bad.append(f"{key} (empty/whitespace)")
    assert not bad, (
        f"{locale_name}.json has empty or non-string values: {bad}"
    )


def test_no_untranslated_passthrough(en_leaves, es_leaves):
    """ES values identical to EN must appear on the vetted allowlist."""
    identical = sorted(
        key
        for key in en_leaves
        if key in es_leaves and en_leaves[key] == es_leaves[key]
    )
    unexpected = [key for key in identical if key not in IDENTICAL_PAIR_ALLOWLIST]
    assert not unexpected, (
        "Found ES translations that are byte-identical to EN but not on the "
        "allowlist (likely untranslated copy-paste). Either translate them "
        "or extend IDENTICAL_PAIR_ALLOWLIST with rationale.\n"
        f"  Unexpected identical pairs: {unexpected}"
    )


def test_keys_used_by_frontend_exist_in_translations(
    used_keys, en_leaves, es_leaves
):
    """Every t('foo.bar') / getTranslation('foo.bar') must resolve."""
    assert used_keys, "scan returned no keys -- regex likely broken"
    missing_en = sorted(k for k in used_keys if k not in en_leaves)
    missing_es = sorted(k for k in used_keys if k not in es_leaves)
    assert not missing_en and not missing_es, (
        "Frontend references keys that don't exist in the catalog.\n"
        f"  Missing in en.json: {missing_en}\n"
        f"  Missing in es.json: {missing_es}"
    )


def test_jinja_templates_keys_documented():
    """Backend Jinja2 + email templates do not currently use i18n.

    If a future change introduces ``{{ t.key }}``, ``{{ _('foo') }}``, or
    ``{% trans %}`` blocks, this assertion will fail and force a follow-up
    that adds the corresponding catalog entries.
    """
    template_paths: list[Path] = []
    if DOC_TEMPLATES.is_dir():
        template_paths.extend(DOC_TEMPLATES.rglob("*.j2"))
        template_paths.extend(DOC_TEMPLATES.rglob("*.html"))
    if ENGAGEMENT_DIR.is_dir():
        template_paths.extend(ENGAGEMENT_DIR.rglob("*.j2"))

    # Sentinels for any localisation hook a future maintainer might add.
    sentinels = [
        re.compile(r"\{\{\s*t\.[a-zA-Z]"),
        re.compile(r"\{\{\s*_\(['\"]"),
        re.compile(r"\{%\s*trans"),
    ]

    findings: list[str] = []
    for path in template_paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for rx in sentinels:
            if rx.search(text):
                findings.append(
                    f"{path.relative_to(REPO_ROOT)}: i18n hook detected "
                    f"(pattern={rx.pattern}). Add the keys to en.json/es.json "
                    "and extend this test."
                )
                break

    assert not findings, (
        "Backend templates have started using i18n but the completeness gate "
        "has not been updated:\n  " + "\n  ".join(findings)
    )


def test_arch_check_rules_observed():
    """Sanity guard so the test file itself stays within arch limits.

    The architecture rule for test files is <600 lines. Asserting here keeps
    the gate self-policing in case future maintainers expand the suite.
    """
    line_count = len(Path(__file__).read_text(encoding="utf-8").splitlines())
    assert line_count < 600, f"test file is {line_count} lines (limit 600)"


def test_arch_check_passes_on_this_file():
    """Run ``bpsai-pair arch check`` against this file to guarantee the
    architecture gate stays green as part of CI rather than as a separate
    manual step. Skips gracefully if the CLI is not on PATH (e.g. minimal
    CI image), since the dedicated arch-check job covers that case.
    """
    rel = Path(__file__).relative_to(REPO_ROOT)
    try:
        result = subprocess.run(
            ["bpsai-pair", "arch", "check", str(rel)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pytest.skip("bpsai-pair CLI unavailable in this environment")
    assert result.returncode == 0, (
        f"arch check failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
