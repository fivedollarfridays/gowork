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


@pytest.mark.parametrize("locale_name", ["en", "es"])
def test_no_empty_values(locale_name, en_leaves, es_leaves):
    """No leaf value may be empty, whitespace-only, or a non-string type."""
    leaves = en_leaves if locale_name == "en" else es_leaves
    bad: list[str] = []
    for key, value in leaves.items():
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
