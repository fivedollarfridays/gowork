"""Key-rotation overlap tests for compliance export tokens (T13.62 follow-up).

Why this file exists
====================

The compliance export tokens (T12.36, :mod:`compliance._export_tokens`)
mirror the manage-appointment token kid-rotation pattern: the signed
payload carries ``kid`` so the operator can rotate
``COMPLIANCE_TOKEN_SECRET`` without invalidating download links that
have already been minted into recent right-to-export emails.

The T13.62 driver fixed a token-downgrade hole in the appointment
verifier: the original logic accepted any kid that was not literally
``"old"`` by falling through to "try every active secret", which let an
attacker tag a forged token ``kid='future'``, sign it under a deployed
secret, and slip past the verifier. The same bug pattern is present
here. This file pins the desired post-fix behaviour:

* ``test_unknown_kid_rejected`` — a forged ``kid='future'`` token signed
  with the live secret must reject (``ComplianceTokenError``).
* ``test_current_kid_accepted`` — round-trip baseline; a freshly-signed
  ``kid='current'`` token verifies. This protects against an over-eager
  fix that accidentally rejects the happy path.
* ``test_old_kid_accepted_with_old_secret`` — a token signed under the
  old secret with ``kid='old'`` verifies while
  ``COMPLIANCE_TOKEN_SECRET_OLD`` is set (mid-rotation overlap window).
* ``test_old_kid_rejected_without_old_secret`` — once the operator
  retires OLD, an old-kid token must reject (no fall-through to
  the active secret pool).

Both secrets are monkeypatched per-test; the production env is not
touched. We hand-mint tokens carrying the desired kid via
``_hand_mint_token`` because the public ``sign_export_token`` only ever
stamps ``kid='current'``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.core.migrations import runner
from tests._fake_clock import freeze_time

# ------------------------------------------------------------------ fixtures

_SECRET_NEW = "export-new-secret-rotation-tests-0123456789abcdef"
_SECRET_OLD = "export-old-secret-rotation-tests-fedcba9876543210"


@pytest.fixture
def migrated_db(tmp_path: Path) -> str:
    """Temp SQLite DB with every migration applied (incl. used_tokens)."""
    db_path = str(tmp_path / "export-rotation.db")
    runner.apply_pending(db_path)
    return db_path


@pytest.fixture
def both_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mid-rotation: both NEW (current) and OLD env vars are set."""
    monkeypatch.setenv("COMPLIANCE_TOKEN_SECRET", _SECRET_NEW)
    monkeypatch.setenv("COMPLIANCE_TOKEN_SECRET_OLD", _SECRET_OLD)


@pytest.fixture
def only_new_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """Post-rotation: OLD has been retired."""
    monkeypatch.setenv("COMPLIANCE_TOKEN_SECRET", _SECRET_NEW)
    monkeypatch.delenv("COMPLIANCE_TOKEN_SECRET_OLD", raising=False)


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _hand_mint_token(
    *,
    secret: str,
    sid: str,
    arc: str,
    kid: str,
    iat: int,
    exp: int,
) -> str:
    """Build a token with an explicit ``kid`` + secret pair.

    Production ``sign_export_token`` only ever stamps ``kid='current'``;
    the rotation tests need ``kid='old'`` (issued before a rotation) and
    ``kid='future'`` (forgery probe), which requires bypassing the
    public signer.
    """
    payload = {
        "sid": sid,
        "arc": arc,
        "exp": int(exp),
        "iat": int(iat),
        "kid": kid,
    }
    encoded = _b64url(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    )
    sig = hmac.new(
        secret.encode("utf-8"),
        encoded.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{encoded}.{_b64url(sig)}"


# ------------------------------------------------------------------ tests


def test_current_kid_accepted(
    migrated_db: str, both_secrets: None,
) -> None:
    """A freshly-signed kid='current' token verifies. Happy-path baseline."""
    from app.modules.compliance import _export_tokens as et

    token = et.sign_export_token("sess-current", archive_id="arc-current")
    sid, arc = et.verify_export_token(token, db_path=migrated_db)
    assert sid == "sess-current"
    assert arc == "arc-current"


def test_old_kid_accepted_with_old_secret(
    migrated_db: str, both_secrets: None,
) -> None:
    """A token signed under OLD with kid='old' verifies during overlap."""
    from app.modules.compliance import _export_tokens as et

    iat = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
    exp = iat + 12 * 3600  # well within the 24h TTL

    old_kid_token = _hand_mint_token(
        secret=_SECRET_OLD,
        sid="sess-old",
        arc="arc-old",
        kid="old",
        iat=iat,
        exp=exp,
    )

    # Freeze inside the TTL so failure cannot be attributed to expiry.
    with freeze_time("2026-04-01T06:00:00+00:00"):
        sid, arc = et.verify_export_token(old_kid_token, db_path=migrated_db)
    assert sid == "sess-old"
    assert arc == "arc-old"


def test_old_kid_rejected_without_old_secret(
    migrated_db: str, only_new_secret: None,
) -> None:
    """Once OLD is retired, an old-kid token must reject as
    ``ComplianceTokenError`` — there is no remaining secret in the
    verifier pool that can match its signature.
    """
    from app.modules.compliance import _export_tokens as et

    iat = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
    exp = iat + 12 * 3600  # well within TTL — failure is not expiry.

    old_kid_token = _hand_mint_token(
        secret=_SECRET_OLD,
        sid="sess-stranded",
        arc="arc-stranded",
        kid="old",
        iat=iat,
        exp=exp,
    )

    with freeze_time("2026-04-01T06:00:00+00:00"):
        with pytest.raises(et.ComplianceTokenError):
            et.verify_export_token(old_kid_token, db_path=migrated_db)


def test_unknown_kid_rejected(
    migrated_db: str, both_secrets: None,
) -> None:
    """A token whose kid is neither 'current' nor 'old' must reject.

    The verifier should not accept a forged kid even if the attacker
    signs the payload with one of the deployed secrets — the kid is
    part of the signed payload and is the authority for which secret
    pool to consult. Mirrors the appointment-token T13.62 hardening.

    Pre-fix the verifier falls through to the full active-secret pool
    for any kid that is not literally ``"old"``, so the NEW-signed
    forgery would pass. We freeze inside the TTL so a pass cannot be
    masked by an expiry rejection.
    """
    from app.modules.compliance import _export_tokens as et

    iat = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
    exp = iat + 12 * 3600

    # Sign with the live NEW secret but tag kid='future'.
    forged = _hand_mint_token(
        secret=_SECRET_NEW,
        sid="sess-forged",
        arc="arc-forged",
        kid="future",
        iat=iat,
        exp=exp,
    )

    with freeze_time("2026-04-01T06:00:00+00:00"):
        with pytest.raises(et.ComplianceTokenError):
            et.verify_export_token(forged, db_path=migrated_db)
