"""Tests for the boot-time required-env-var validator (T13.118).

The validator must:
* Read from ``os.environ`` directly (not the ``Settings`` cache) so
  monkeypatching the env in fixtures works deterministically.
* Raise ``RuntimeError`` with the offending var name when a required
  var is missing — never log the value.
* Warn but not raise when an optional but behavior-affecting var is
  missing (LLM keys, SendGrid, BrightData, etc.).
* Be idempotent and side-effect-free apart from logging.
"""

from __future__ import annotations

import logging
import os

import pytest

from app.core.env_validation import (
    OPTIONAL_BEHAVIOR_VARS,
    REQUIRED_BOOT_VARS,
    validate_required_env,
)


@pytest.fixture
def clean_env(monkeypatch):
    """Yield a fixture that wipes every var the validator inspects.

    Using monkeypatch.delenv with raising=False means the underlying
    process env is restored automatically after the test.
    """
    for key in REQUIRED_BOOT_VARS + OPTIONAL_BEHAVIOR_VARS:
        monkeypatch.delenv(key, raising=False)
    return monkeypatch


def _set_all_required(monkeypatch) -> None:
    """Populate every required var with a non-empty placeholder."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    monkeypatch.setenv("ADMIN_API_KEY", "x" * 32)
    monkeypatch.setenv("AUDIT_HASH_SALT", "test-salt-not-default")


# -------------------- Cycle 1: happy path --------------------


def test_all_required_vars_present_does_not_raise(clean_env):
    """Every required var set → validator returns without error."""
    _set_all_required(clean_env)
    validate_required_env()  # Must not raise.


# -------------------- Cycle 2: missing DATABASE_URL --------------------


def test_missing_database_url_raises_runtime_error(clean_env):
    """Missing DATABASE_URL → RuntimeError naming the var."""
    _set_all_required(clean_env)
    clean_env.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError) as excinfo:
        validate_required_env()
    assert "DATABASE_URL" in str(excinfo.value)


# -------------------- Cycle 3: missing ADMIN_API_KEY --------------------


def test_missing_admin_api_key_raises_runtime_error(clean_env):
    """Missing ADMIN_API_KEY → RuntimeError naming the var."""
    _set_all_required(clean_env)
    clean_env.delenv("ADMIN_API_KEY", raising=False)
    with pytest.raises(RuntimeError) as excinfo:
        validate_required_env()
    assert "ADMIN_API_KEY" in str(excinfo.value)


def test_empty_admin_api_key_raises_runtime_error(clean_env):
    """Empty-string ADMIN_API_KEY also fails — silent default risk."""
    _set_all_required(clean_env)
    clean_env.setenv("ADMIN_API_KEY", "")
    with pytest.raises(RuntimeError) as excinfo:
        validate_required_env()
    assert "ADMIN_API_KEY" in str(excinfo.value)


# -------------------- Cycle 4: missing AUDIT_HASH_SALT --------------------


def test_missing_audit_hash_salt_raises_runtime_error(clean_env):
    """Missing AUDIT_HASH_SALT → RuntimeError naming the var."""
    _set_all_required(clean_env)
    clean_env.delenv("AUDIT_HASH_SALT", raising=False)
    with pytest.raises(RuntimeError) as excinfo:
        validate_required_env()
    assert "AUDIT_HASH_SALT" in str(excinfo.value)


# -------------------- Cycle 5: optional vars warn but never raise --------------------


def test_optional_var_missing_warns_but_does_not_raise(
    clean_env, caplog: pytest.LogCaptureFixture
):
    """Missing optional vars (LLM, SendGrid, etc.) log warnings only."""
    _set_all_required(clean_env)
    for key in OPTIONAL_BEHAVIOR_VARS:
        clean_env.delenv(key, raising=False)

    with caplog.at_level(logging.WARNING, logger="app.core.env_validation"):
        validate_required_env()  # Must not raise.

    # At least one warning per missing optional var (subset check —
    # we only care that the validator is *talking* about them).
    warning_text = "\n".join(rec.getMessage() for rec in caplog.records)
    assert "ANTHROPIC_API_KEY" in warning_text
    assert "SENDGRID_API_KEY" in warning_text


def test_optional_var_present_does_not_warn(
    clean_env, caplog: pytest.LogCaptureFixture
):
    """When optional vars are set, no missing-optional warning is emitted."""
    _set_all_required(clean_env)
    for key in OPTIONAL_BEHAVIOR_VARS:
        clean_env.setenv(key, "set-for-test")

    with caplog.at_level(logging.WARNING, logger="app.core.env_validation"):
        validate_required_env()

    warning_text = "\n".join(rec.getMessage() for rec in caplog.records)
    # No "missing optional" complaints.
    assert "missing" not in warning_text.lower()


# -------------------- Cycle 6: reads from os.environ (not Settings cache) --------------------


def test_validator_reads_from_os_environ_not_settings_cache(clean_env):
    """The validator must consult os.environ live so test fixtures work.

    If it cached or read through Settings, the monkeypatch.delenv would
    be invisible after the first import.
    """
    _set_all_required(clean_env)
    # Confirm baseline: passes.
    validate_required_env()

    # Now remove a required var via the same mechanism a fixture uses.
    clean_env.delenv("DATABASE_URL", raising=False)
    assert "DATABASE_URL" not in os.environ
    with pytest.raises(RuntimeError):
        validate_required_env()


def test_required_secret_value_never_appears_in_error_message(clean_env):
    """Audit-trail safety: error mentions var NAME, not its value."""
    _set_all_required(clean_env)
    sentinel = "DEADBEEF-secret-do-not-log-12345"
    clean_env.setenv("ADMIN_API_KEY", sentinel)
    # Now invalidate by clearing it — but verify even when set, no
    # validator log path leaks the value.
    clean_env.delenv("AUDIT_HASH_SALT", raising=False)
    with pytest.raises(RuntimeError) as excinfo:
        validate_required_env()
    assert sentinel not in str(excinfo.value)
