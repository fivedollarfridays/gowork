"""Charter integrity: matching engine reads ZERO Dallas-specific signals.

Sprint 25 (Dallas Expansion / DFW Unification) is *additive*. The existing
`get_city_config()` dispatch keys on `city.state == "TX"` across 10+ modules,
so Dallas inherits all TX state-level work for free. This test pins the
load-bearing invariant: the matching engine remains city-symmetric — no
metro-special-case, no Dallas-aware branching.

If a future sprint legitimately needs cross-metro matching (a Dallas resident
seeing FW jobs, an FW resident seeing DART transit, etc.), THIS TEST IS THE
DESIGN-REVIEW TRIGGER. The right path is:

    1. Read this docstring + the brief at
       .paircoder/plans/briefs/brief-sprint-25-dallas-expansion.md
    2. Open a sprint that consciously breaks the invariant
       (employer-index unification, geo-radius extension, etc.)
    3. Update this test's `_PINNED_*` allowlists with the new
       cross-metro entries + a comment explaining the design decision.

Inheriting the S24 pattern (see test_listing_verification_e2e.py's
"CHARTER INTEGRITY ASSERTION" block).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MATCHING_DIR = _REPO_ROOT / "backend" / "app" / "modules" / "matching"

# Forbidden tokens — any reference to these in the matching engine is a
# charter violation by default. Case-insensitive.
_FORBIDDEN_TOKENS = (
    r"\bdallas\b",       # city slug + city name
    r"\bDART\b",          # transit operator (case-sensitive on the all-caps form)
    r"\bDFW\b",           # metro abbreviation
)

# Embedded Dallas ZIPs (T25.6's bbox extension). Matching engine must not
# special-case these either.
_FORBIDDEN_DALLAS_ZIPS = (
    "75201", "75204", "75215", "75216", "75217",
    "75224", "75227", "75228", "75232", "75241",
)

# If a legitimate future use surfaces (e.g., a multi-city test fixture
# imported into matching code), allowlist the (file, token) pair here with
# a brief reason. Keep this list small; the goal is design-review pressure,
# not blanket suppression.
_PINNED_ALLOWLIST: tuple[tuple[str, str, str], ...] = (
    # (relative_path, token_regex, reason)
)


def _matching_py_files() -> list[Path]:
    """Every Python file under backend/app/modules/matching/."""
    return sorted(p for p in _MATCHING_DIR.rglob("*.py") if p.is_file())


def _matching_files_exist() -> bool:
    """Sanity: the matching engine directory must exist (S5+ artifact)."""
    return _MATCHING_DIR.is_dir() and any(_MATCHING_DIR.rglob("*.py"))


@pytest.mark.skipif(
    not _matching_files_exist(),
    reason="matching engine directory missing — investigate before running",
)
def test_matching_engine_has_no_dallas_token_references() -> None:
    """Grep across backend/app/modules/matching/ for forbidden tokens. Any
    match is a charter violation — see module docstring for the design-review
    path if this test fails legitimately.
    """
    violations: list[str] = []
    for token_pattern in _FORBIDDEN_TOKENS:
        flags = re.IGNORECASE if token_pattern == r"\bdallas\b" else 0
        regex = re.compile(token_pattern, flags)
        for path in _matching_py_files():
            text = path.read_text(encoding="utf-8", errors="replace")
            for line_no, line in enumerate(text.splitlines(), start=1):
                if not regex.search(line):
                    continue
                rel = str(path.relative_to(_REPO_ROOT))
                if (rel, token_pattern, _ANY_REASON) in _PINNED_ALLOWLIST:
                    continue
                allowlisted = any(
                    a_path == rel and a_token == token_pattern
                    for a_path, a_token, _reason in _PINNED_ALLOWLIST
                )
                if allowlisted:
                    continue
                violations.append(f"{rel}:{line_no}: {line.strip()}")

    assert not violations, (
        "Charter violation — matching engine references Dallas-specific "
        "tokens. The display-only invariant requires the matching engine "
        "to remain city-symmetric. See test_charter_integrity_dallas.py "
        "module docstring for the design-review path.\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


@pytest.mark.skipif(
    not _matching_files_exist(),
    reason="matching engine directory missing — investigate before running",
)
def test_matching_engine_has_no_dallas_zip_references() -> None:
    """Grep for embedded Dallas ZIPs (75201, 75204, etc.). Same charter
    invariant — matching engine must not special-case any specific Dallas
    ZIP code. ZIP-to-city resolution is the canonical entry point; matching
    happens against city.state, not zip.
    """
    violations: list[str] = []
    for zip_code in _FORBIDDEN_DALLAS_ZIPS:
        for path in _matching_py_files():
            text = path.read_text(encoding="utf-8", errors="replace")
            for line_no, line in enumerate(text.splitlines(), start=1):
                # Word-boundary match so 752015 doesn't false-positive
                # on 75201. Real GTFS / data files use the bare 5-digit form.
                if re.search(rf"\b{zip_code}\b", line):
                    rel = str(path.relative_to(_REPO_ROOT))
                    violations.append(f"{rel}:{line_no}: {line.strip()}")

    assert not violations, (
        "Charter violation — matching engine references specific Dallas "
        "ZIP codes. ZIP-to-city resolution is canonical; matching dispatches "
        "on city.state, not on individual ZIPs. See module docstring.\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


def test_subprocess_grep_agrees_with_in_python_grep() -> None:
    """Belt-and-suspenders: the in-Python grep above is the authoritative
    test, but cross-check with a subprocess `grep -rIn` to catch the case
    where someone adds a binary file or a build artifact under
    matching/ that the python globber would skip but a CI grep job would
    flag. Same allowlist semantics.
    """
    if not _matching_files_exist():
        pytest.skip("matching engine directory missing")
    # Combined regex: dallas|DART|DFW|<zip>|<zip>|...
    pattern = "|".join(
        ("[Dd]allas", "DART", "DFW", *(rf"\b{z}\b" for z in _FORBIDDEN_DALLAS_ZIPS))
    )
    result = subprocess.run(  # noqa: S603 - controlled args, no shell
        ["grep", "-rEIn", "--include=*.py", pattern, str(_MATCHING_DIR)],
        capture_output=True,
        text=True,
        check=False,
    )
    # grep exit 0 = matches found (bad); 1 = no matches (good); 2 = error
    assert result.returncode in (0, 1), (
        f"grep failed unexpectedly: stderr={result.stderr!r}"
    )
    if result.returncode == 0:
        # Filter against allowlist before failing
        lines = [
            ln for ln in result.stdout.strip().splitlines()
            if not any(
                f"/{a_path}:" in ln for a_path, _t, _r in _PINNED_ALLOWLIST
            )
        ]
        assert not lines, (
            "subprocess grep found Dallas-specific tokens in matching/:\n"
            + "\n".join(f"  - {ln}" for ln in lines)
        )


# Sentinel used by the in-python grep to make the allowlist tuple
# (path, regex, reason) lookup explicit when reason is irrelevant.
_ANY_REASON = object()
