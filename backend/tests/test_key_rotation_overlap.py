"""Key-rotation overlap tests for the manage-appointment HMAC tokens (T13.62).

Why this file exists
====================

The appointment manage-link tokens (S12b T12.10b) embed a ``kid`` field
in the signed payload so the signing secret can be rotated without
stranding outstanding email links. The runbook in
``docs/ops/appointment-token-rotation.md`` documents a **7-day overlap
window** during which both the new and old secrets are accepted: long
enough for every previously-issued token (which inherits the 7-day TTL)
to expire naturally.

This test file pins the overlap contract so a regression cannot silently
land:

* ``test_current_kid_always_accepts`` — the no-rotation happy path; the
  current secret signs and verifies a token across the full TTL window.
* ``test_old_kid_accepts_within_overlap`` — operator has set both
  ``APPOINTMENT_TOKEN_SECRET`` (new) and ``APPOINTMENT_TOKEN_SECRET_OLD``
  (old); a token minted before the rotation must still verify.
* ``test_old_kid_rejects_after_overlap`` — operator has retired the
  OLD secret per the runbook step 6; previously-valid old-kid tokens
  must now reject (TokenInvalid, no enumeration oracle).
* ``test_both_kids_accept_during_overlap`` — both kids verify
  concurrently while OLD is set; required so rolling deploys do not
  drop traffic.
* ``test_unknown_kid_rejected`` — a token whose ``kid`` is neither
  ``current`` nor ``old`` must reject. Defends against an attacker
  forging a kid that we have not yet rotated to.
* ``test_kid_in_payload_not_signature`` — flipping the kid (without
  re-signing) must invalidate the signature. Defends against
  kid-substitution / downgrade attacks.
* ``test_rotation_window_documented`` — pins the 7-day overlap
  constant so the runbook and the code agree.

Both secrets are monkeypatched per-test; production env is not touched.
The fake clock is used to advance time across the TTL boundary without
sleeping in real time.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core.migrations import runner
from tests._fake_clock import freeze_time

# ------------------------------------------------------------------ fixtures

_SECRET_NEW = "new-secret-rotation-overlap-tests-0123456789abcdef"
_SECRET_OLD = "old-secret-rotation-overlap-tests-fedcba9876543210"
_SECRET_FUTURE = "future-secret-not-yet-deployed-aaaabbbbccccdddd"


@pytest.fixture
def migrated_db(tmp_path: Path) -> str:
    """Temp SQLite DB with every migration applied (incl. used_tokens)."""
    db_path = str(tmp_path / "rotation.db")
    runner.apply_pending(db_path)
    return db_path


@pytest.fixture
def both_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mid-rotation: both NEW (current) and OLD env vars are set."""
    monkeypatch.setenv("APPOINTMENT_TOKEN_SECRET", _SECRET_NEW)
    monkeypatch.setenv("APPOINTMENT_TOKEN_SECRET_OLD", _SECRET_OLD)


@pytest.fixture
def only_new_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """Post-rotation: OLD has been retired per runbook step 6."""
    monkeypatch.setenv("APPOINTMENT_TOKEN_SECRET", _SECRET_NEW)
    monkeypatch.delenv("APPOINTMENT_TOKEN_SECRET_OLD", raising=False)


def _seed_appointment(db_path: str, session_id: str = "rot-sess") -> int:
    """Seed a session + scheduled appointment, return its id."""
    conn = sqlite3.connect(db_path)
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        expires_iso = (
            datetime.now(timezone.utc) + timedelta(days=60)
        ).isoformat()
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, now_iso, "[]", expires_iso),
        )
        starts = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        ends = (
            datetime.now(timezone.utc) + timedelta(days=3, hours=1)
        ).isoformat()
        cur = conn.execute(
            "INSERT INTO appointments "
            "(session_id, type, title, starts_at, ends_at, location_name, "
            "status, source, created_at) "
            "VALUES (?, 'dmv', 'Rotation', ?, ?, 'DMV', 'scheduled', "
            "'user', ?)",
            (session_id, starts, ends, now_iso),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _hand_mint_token(
    *,
    secret: str,
    aid: int,
    action: str,
    kid: str,
    iat: int,
    exp: int,
) -> str:
    """Build a token with an explicit kid + secret pair.

    The production ``sign`` function only ever stamps ``kid='current'``;
    these tests need to mint tokens carrying ``kid='old'`` (issued before
    a rotation) and ``kid='future'`` (forgery probe), which requires
    bypassing the public signer.
    """
    payload = {
        "aid": int(aid),
        "act": action,
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


def test_current_kid_always_accepts(
    migrated_db: str, both_secrets: None,
) -> None:
    """Sign with the current kid; token verifies immediately and far into
    the TTL window. This is the no-rotation happy path baseline.

    Each call to ``verify`` consumes the token (m004 single-use), so we
    seed a separate appointment per probe — same secret, distinct
    payload bytes, distinct token hash.
    """
    from app.modules.appointments import tokens

    aid_immediate = _seed_appointment(migrated_db, session_id="rot-imm")
    aid_late = _seed_appointment(migrated_db, session_id="rot-late")
    start = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)

    with freeze_time(start) as clock:
        # Immediate verify: kid="current" + the NEW secret matches.
        token = tokens.sign(aid_immediate, tokens.TokenAction.VIEW)
        assert tokens.verify(
            token, tokens.TokenAction.VIEW, db_path=migrated_db,
        ) == aid_immediate

        # Mint a token at t=start, then advance ~6 days (still inside the
        # 7-day TTL); the older token must still verify.
        late_token = tokens.sign(
            aid_late, tokens.TokenAction.VIEW, now=start,
        )
        clock.advance(6 * 24 * 3600)
        assert tokens.verify(
            late_token, tokens.TokenAction.VIEW, db_path=migrated_db,
        ) == aid_late


def test_old_kid_accepts_within_overlap(
    migrated_db: str, both_secrets: None,
) -> None:
    """A token bearing kid='old' signed under the OLD secret verifies
    while OLD is still set. Simulates: user clicks a manage-link from
    an email sent just before the operator rotated the secret."""
    from app.modules.appointments import tokens

    aid = _seed_appointment(migrated_db)
    iat = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
    exp = iat + 6 * 24 * 3600  # 6 days — comfortably inside the TTL.

    old_kid_token = _hand_mint_token(
        secret=_SECRET_OLD, aid=aid, action="cancel",
        kid="old", iat=iat, exp=exp,
    )

    # The runbook's "mid-rotation" state: NEW is current, OLD is set.
    with freeze_time("2026-04-02T00:00:00+00:00"):
        result = tokens.verify(
            old_kid_token, tokens.TokenAction.CANCEL, db_path=migrated_db,
        )
        assert result == aid


def test_old_kid_rejects_after_overlap(
    migrated_db: str, only_new_secret: None,
) -> None:
    """After runbook step 6 (operator unsets OLD), an old-kid token
    must reject as ``TokenInvalid`` — there is no remaining secret in
    the verifier pool that can match its signature."""
    from app.modules.appointments import tokens

    aid = _seed_appointment(migrated_db)
    iat = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
    exp = iat + 6 * 24 * 3600  # well within TTL — failure is *not* expiry.

    old_kid_token = _hand_mint_token(
        secret=_SECRET_OLD, aid=aid, action="view",
        kid="old", iat=iat, exp=exp,
    )

    with freeze_time("2026-04-02T00:00:00+00:00"):
        with pytest.raises(tokens.TokenInvalid):
            tokens.verify(
                old_kid_token, tokens.TokenAction.VIEW, db_path=migrated_db,
            )


def test_both_kids_accept_during_overlap(
    migrated_db: str, both_secrets: None,
) -> None:
    """Tokens bearing kid='current' AND tokens bearing kid='old' both
    verify while the operator's env carries both secrets. Required for
    rolling deploys: a worker mid-flight must not see a dead link."""
    from app.modules.appointments import tokens

    aid_current = _seed_appointment(migrated_db, session_id="rot-cur")
    aid_old = _seed_appointment(migrated_db, session_id="rot-old")
    iat = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
    exp = iat + 6 * 24 * 3600

    with freeze_time("2026-04-02T00:00:00+00:00"):
        # Newly-minted token (kid='current', signed under NEW secret).
        current_token = tokens.sign(aid_current, tokens.TokenAction.VIEW)
        # Hand-built old-kid token (signed under OLD secret).
        old_token = _hand_mint_token(
            secret=_SECRET_OLD, aid=aid_old, action="view",
            kid="old", iat=iat, exp=exp,
        )

        assert tokens.verify(
            current_token, tokens.TokenAction.VIEW, db_path=migrated_db,
        ) == aid_current
        assert tokens.verify(
            old_token, tokens.TokenAction.VIEW, db_path=migrated_db,
        ) == aid_old


def test_unknown_kid_rejected(
    migrated_db: str, both_secrets: None,
) -> None:
    """A token whose ``kid`` is neither 'current' nor 'old' must reject.

    The verifier should not accept a forged kid even if the attacker
    signs the payload with one of the deployed secrets — the kid is
    part of the signed payload and is the authority for which secret
    pool to consult. Today the implementation tolerates *any* kid that
    is not literally ``"old"`` (it falls through to the full active
    pool), which means a token tagged ``kid='future'`` and signed with
    the NEW secret would currently pass. This test pins the desired
    behaviour for follow-up hardening.
    """
    from app.modules.appointments import tokens

    aid = _seed_appointment(migrated_db)
    iat = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
    exp = iat + 6 * 24 * 3600

    # Sign with the deployed NEW secret but tag kid='future'.
    forged = _hand_mint_token(
        secret=_SECRET_NEW, aid=aid, action="view",
        kid="future", iat=iat, exp=exp,
    )

    with freeze_time("2026-04-02T00:00:00+00:00"):
        with pytest.raises(tokens.TokenInvalid):
            tokens.verify(
                forged, tokens.TokenAction.VIEW, db_path=migrated_db,
            )


def test_kid_in_payload_not_signature(
    migrated_db: str, both_secrets: None,
) -> None:
    """The ``kid`` is part of the signed payload, so swapping kids
    invalidates the signature.

    Attack scenario: attacker captures a kid='old' token (signed under
    OLD), wants to forge a kid='current' equivalent without knowing
    NEW. Mutating the kid byte-flips the JSON, the encoded payload
    differs, and the precomputed HMAC no longer matches.
    """
    from app.modules.appointments import tokens

    aid = _seed_appointment(migrated_db)
    iat = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
    exp = iat + 6 * 24 * 3600

    legit_old = _hand_mint_token(
        secret=_SECRET_OLD, aid=aid, action="view",
        kid="old", iat=iat, exp=exp,
    )

    # Decode payload, flip kid -> "current", re-encode (without
    # re-signing). Reuse the original signature.
    encoded, original_sig = legit_old.split(".", 1)
    padding = "=" * (-len(encoded) % 4)
    payload_dict = json.loads(
        base64.urlsafe_b64decode(encoded + padding).decode("utf-8")
    )
    assert payload_dict["kid"] == "old"
    payload_dict["kid"] = "current"
    swapped_encoded = _b64url(
        json.dumps(
            payload_dict, separators=(",", ":"), sort_keys=True,
        ).encode()
    )
    forged = f"{swapped_encoded}.{original_sig}"

    with freeze_time("2026-04-02T00:00:00+00:00"):
        with pytest.raises(tokens.TokenInvalid):
            tokens.verify(
                forged, tokens.TokenAction.VIEW, db_path=migrated_db,
            )


def test_rotation_window_documented() -> None:
    """A constant in the tokens module must pin the documented
    7-day overlap window so docs and code cannot drift.

    The runbook (docs/ops/appointment-token-rotation.md, section 2
    step 5) instructs operators to wait "at least 7 days" before
    retiring OLD. That interval is identical to the default token
    TTL — an outstanding token cannot survive past TTL, so retiring
    OLD after 7 days is provably safe. We pin both the days constant
    and the seconds-equivalence to the TTL.
    """
    from app.modules.appointments import tokens

    overlap_days = getattr(tokens, "KEY_ROTATION_OVERLAP_DAYS", None)
    assert overlap_days == 7, (
        "KEY_ROTATION_OVERLAP_DAYS must equal the documented "
        "7-day rotation overlap window (see appointment-token-rotation.md)"
    )
    # The overlap window must be at least the default token TTL, else
    # tokens minted just before rotation could be stranded.
    assert overlap_days * 24 * 3600 >= tokens._DEFAULT_TTL_SEC
