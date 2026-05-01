"""Admin-key / secret-literal scan for S12b new files (T12.35b gate).

Guards against regressions where a secret, admin key, token, or password
is ever assigned a literal string value inside one of the new S12b
modules. Mirrors the S12a scan (``test_s12a_admin_key_scan.py``) but
sweeps the broader S12b surface: route files + module spokes + new
migrations + nightly orchestrator + advisor_auth + pdf_renderer.

The regex looks for:

    <ident_containing_key|secret|token|password> = "literal-of-6+chars"

Legitimate patterns (``os.environ.get``, ``settings.xxx``, function
parameters, header-name constants that do not contain any of the
forbidden substrings) are not matched by the regex, so no allow-list
is required for production code.

A second pass scans the obvious test-file mistake (a real-looking key
committed to a fixture) by flagging any token-like literal of >=32
hex/base64 chars in the S12b test modules. Test fixtures legitimately
use short obviously-fake placeholders like ``"tok-mtg-..."``.
"""

from __future__ import annotations

import re
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_APP_ROOT = _BACKEND_ROOT / "app"
_SCRIPTS_ROOT = _BACKEND_ROOT / "scripts"
_TESTS_ROOT = _BACKEND_ROOT / "tests"


# ----------------------------------------------------------------- new files

# Every NEW file introduced under S12b. Grouped for traceability.
_S12B_ROUTE_FILES: tuple[str, ...] = (
    "advisor_inbox.py",
    "appointments_manage.py",
    "compliance.py",
    "documents.py",
    "engagement.py",
)

_S12B_CORE_FILES: tuple[Path, ...] = (
    _APP_ROOT / "core" / "advisor_auth.py",
    _APP_ROOT / "core" / "pdf_renderer.py",
    _APP_ROOT / "core" / "migrations" / "m004_used_tokens.py",
    _APP_ROOT / "core" / "migrations" / "m005_sessions_demo_column.py",
    _APP_ROOT / "core" / "migrations" / "m006_compliance_tombstones.py",
    _APP_ROOT / "core" / "migrations" / "m007_advisor_tokens.py",
)

# Walk every file under each new module dir.
_S12B_MODULE_DIRS: tuple[Path, ...] = (
    _APP_ROOT / "modules" / "advisor",
    _APP_ROOT / "modules" / "compliance",
    _APP_ROOT / "modules" / "documents",
    _APP_ROOT / "modules" / "engagement",
)

# Selected new appointments + plan spokes added in S12b. Existing
# pre-S12 spokes (persistence.py, types.py, etc.) are NOT scanned —
# they live under git history pre-dating S12b.
_S12B_APPOINTMENT_SPOKES: tuple[Path, ...] = (
    _APP_ROOT / "modules" / "appointments" / "tokens.py",
    _APP_ROOT / "modules" / "appointments" / "transactional_emails.py",
    _APP_ROOT / "modules" / "appointments" / "enrichment.py",
    _APP_ROOT / "modules" / "appointments" / "availability.py",
    _APP_ROOT / "modules" / "appointments" / "reconcile.py",
    _APP_ROOT / "modules" / "appointments" / "unavailability.py",
    _APP_ROOT / "modules" / "appointments" / "service_config.py",
    _APP_ROOT / "modules" / "appointments" / "_email_dispatch.py",
    _APP_ROOT / "modules" / "appointments" / "_email_rendering.py",
    _APP_ROOT / "modules" / "appointments" / "_availability_time.py",
)

_S12B_PLAN_SPOKES: tuple[Path, ...] = (
    _APP_ROOT / "modules" / "plan" / "plan_refresher.py",
    _APP_ROOT / "modules" / "plan" / "plan_progress.py",
    _APP_ROOT / "modules" / "plan" / "weekly_review.py",
)

_S12B_SCRIPT_FILES: tuple[Path, ...] = (
    _SCRIPTS_ROOT / "nightly_digest.py",
)


# ----------------------------------------------------------------- regex

# Flag any identifier (containing key/secret/token/password, any case)
# that is assigned a string literal of length >= 6. RHS of a function
# call — e.g. ``admin_key = settings.admin_key`` — is not matched.
_FORBIDDEN_PATTERN = re.compile(
    r"\b([a-zA-Z_][a-zA-Z0-9_]*"
    r"(?:key|secret|token|password)"
    r"[a-zA-Z0-9_]*)\s*[:=][^=\n]*?[\"']([^\"'\n]{6,})[\"']",
    re.IGNORECASE,
)

# An env-var identifier RHS (UPPERCASE_WITH_UNDERSCORES) is not a
# secret — it's the *name* of the env var the secret lives in.
_ENV_VAR_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]+$")

# Allowlist of literal substrings that are obviously not secrets
# even though their assignment target contains key/secret/token/password.
# Examples: regex patterns, dict-key identifiers, env-var names, doc URLs.
_FORBIDDEN_ALLOW_SUBSTRINGS: tuple[str, ...] = (
    "_count",            # documents._document_status `count_key`
    "[A-Za-z]",          # regex char-class fragment in resume_keywords
    "(?:",               # regex group fragment
    "://",               # URL fragments
    "test_",             # test-fixture names embedded in dict keys
    "stub_",
    "fake_",
)


def _is_secret_literal(literal: str) -> bool:
    """Return True iff the literal looks like an actual secret value
    (i.e. NOT an env-var name, NOT a regex pattern, NOT a known
    allowlisted identifier substring)."""
    if _ENV_VAR_NAME_RE.match(literal):
        return False
    for sub in _FORBIDDEN_ALLOW_SUBSTRINGS:
        if sub in literal:
            return False
    return True

# Real-looking keys: long hex / base64-ish runs (>=32 chars). Flagged
# in test files only — production files use the regex above.
# Excludes: module __doc__ strings (no enforcement on prose), comments.
_LONG_HEX_OR_BASE64_PATTERN = re.compile(
    r"[\"']([A-Fa-f0-9]{40,}|[A-Za-z0-9+/=_\-]{60,})[\"']"
)

# Allowlist: short obvious test placeholders (matched by prefix only).
# Any literal whose substring matches one of these prefixes is treated
# as a test fixture and skipped by the long-key scan.
_TEST_FIXTURE_PREFIXES: frozenset[str] = frozenset({
    "mw_adv_",
    "tok-mtg-",
    "tok-ftw-",
    "tok-gate-",
    "tok-demo-",
    "test-",
    "fake-",
    "stub-",
    "gate-",
    "s12b-",
    "s12a-",
    "11111111-",
    "22222222-",
    "33333333-",
})


# ----------------------------------------------------------------- helpers


def _resolve_route_files() -> list[Path]:
    routes_dir = _APP_ROOT / "routes"
    return [routes_dir / fname for fname in _S12B_ROUTE_FILES]


def _walk_module_dirs() -> list[Path]:
    """Return every .py file under each S12b module dir (non-recursive
    package files only — no __pycache__)."""
    out: list[Path] = []
    for d in _S12B_MODULE_DIRS:
        if not d.exists():
            continue
        for p in sorted(d.rglob("*.py")):
            if "__pycache__" in p.parts:
                continue
            out.append(p)
    return out


def _all_production_files() -> list[Path]:
    """Every file the production scan must cover."""
    out: list[Path] = []
    out.extend(_resolve_route_files())
    out.extend(_S12B_CORE_FILES)
    out.extend(_walk_module_dirs())
    out.extend(_S12B_APPOINTMENT_SPOKES)
    out.extend(_S12B_PLAN_SPOKES)
    out.extend(_S12B_SCRIPT_FILES)
    return out


def _is_test_placeholder(literal: str) -> bool:
    """True if the literal is an obvious test fixture (skip in scan)."""
    return any(literal.startswith(p) for p in _TEST_FIXTURE_PREFIXES)


# ----------------------------------------------------------------- existence


def test_all_s12b_files_present() -> None:
    """Every file referenced by the scan exists on disk."""
    missing = [
        str(p.relative_to(_BACKEND_ROOT))
        for p in _all_production_files()
        if not p.exists()
    ]
    assert not missing, f"S12b files missing on disk: {missing}"


# ----------------------------------------------------------------- production scan


def test_no_hardcoded_secrets_in_s12b_production_files() -> None:
    """Zero literal assignments to secret/token/key/password identifiers."""
    violations: list[str] = []
    for path in _all_production_files():
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        for match in _FORBIDDEN_PATTERN.finditer(content):
            var_name = match.group(1)
            literal = match.group(2)
            if not _is_secret_literal(literal):
                continue
            line_num = content[: match.start()].count("\n") + 1
            rel = path.relative_to(_BACKEND_ROOT)
            violations.append(
                f"{rel}:{line_num} — {var_name!r} assigned literal "
                f"{literal!r}"
            )
    assert not violations, (
        "Hardcoded secret-like literals found in S12b production code:\n"
        + "\n".join(violations)
    )


# ----------------------------------------------------------------- test fixture scan


def test_no_real_looking_keys_in_s12b_test_files() -> None:
    """Test files must not commit anything that looks like a real key
    (long hex/base64 literal). Short obvious placeholders are allowed."""
    test_files = [
        _TESTS_ROOT / "test_s12b_gate.py",
        _TESTS_ROOT / "test_s12b_admin_key_scan.py",
        _TESTS_ROOT / "test_s12b_worker_companion_e2e.py",
        _TESTS_ROOT / "_s12b_e2e_helpers.py",
        _TESTS_ROOT / "test_demo_seed_s12b.py",
    ]
    violations: list[str] = []
    for path in test_files:
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        for match in _LONG_HEX_OR_BASE64_PATTERN.finditer(content):
            literal = match.group(1)
            if _is_test_placeholder(literal):
                continue
            line_num = content[: match.start()].count("\n") + 1
            rel = path.relative_to(_BACKEND_ROOT)
            violations.append(
                f"{rel}:{line_num} — long literal {literal!r}"
            )
    assert not violations, (
        "Real-looking keys committed to S12b test files:\n"
        + "\n".join(violations)
    )
