"""Admin-key / secret-literal scan for S12a route files (T12.35 gate).

Guards against regressions where a secret, admin key, token, or password
is ever assigned a literal string value inside one of the new S12a route
modules. The regex looks for:

    <ident_containing_key|secret|token|password> = "literal-of-6+chars"

with case-insensitive identifier matching. Any match is an immediate
assertion failure — legitimate patterns (``os.environ.get``,
``settings.xxx``, function parameters, header-name constants that do not
contain any of the forbidden substrings) are not matched by the regex,
so no allow-list is required today.
"""

from __future__ import annotations

import re
from pathlib import Path

_ROUTES_DIR = Path(__file__).resolve().parent.parent / "app" / "routes"

# The five route modules introduced in S12a.
_NEW_ROUTE_FILES: tuple[str, ...] = (
    "admin_flags.py",
    "appointments.py",
    "jobs_applications.py",
    "sendgrid_webhook.py",
    "engagement_preview.py",
)

# Flag any identifier (containing key/secret/token/password, any case)
# that is assigned a string literal of length >= 6. RHS of a function
# call — e.g. ``admin_key = settings.admin_key`` — is not matched.
_FORBIDDEN_PATTERN = re.compile(
    r"\b([a-zA-Z_][a-zA-Z0-9_]*"
    r"(?:key|secret|token|password)"
    r"[a-zA-Z0-9_]*)\s*[:=][^=\n]*?[\"']([^\"'\n]{6,})[\"']",
    re.IGNORECASE,
)


def test_new_route_files_exist() -> None:
    """All five S12a route files are present in app/routes/."""
    missing = [
        fname for fname in _NEW_ROUTE_FILES
        if not (_ROUTES_DIR / fname).exists()
    ]
    assert not missing, f"Missing S12a route files: {missing}"


def test_no_hardcoded_secrets_in_new_route_files() -> None:
    """Zero literal assignments to secret/token/key/password identifiers."""
    violations: list[str] = []
    for fname in _NEW_ROUTE_FILES:
        path = _ROUTES_DIR / fname
        content = path.read_text()
        for match in _FORBIDDEN_PATTERN.finditer(content):
            var_name = match.group(1)
            literal = match.group(2)
            line_num = content[: match.start()].count("\n") + 1
            violations.append(
                f"{fname}:{line_num} — {var_name!r} assigned literal "
                f"{literal!r}"
            )
    assert not violations, (
        "Hardcoded secret-like literals found:\n" + "\n".join(violations)
    )
