"""Feature flag resolution + runtime toggle infrastructure (T12.0b).

Resolution chain for :func:`is_enabled`:

1. Environment variable ``FEATURE_<FLAG_NAME>`` (uppercase, underscores).
   Truthy: ``true``, ``1``, ``yes`` (case-insensitive). Anything else → False.
2. Runtime override written by :func:`set_flag_runtime` (in-memory).
3. ``config/feature_flags.yaml`` entry keyed on ``flag_name``.
4. Caller-supplied ``default`` (``False`` by default).

Runtime toggles (via the admin endpoint) persist an audit row to the
``feature_flag_audit`` table created by migration m002.
"""

from __future__ import annotations

import hashlib
import logging
import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# ``backend/app/core/feature_flags.py`` → project root is 4 parents up.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_YAML_PATH: Path = _PROJECT_ROOT / "config" / "feature_flags.yaml"

_TRUTHY = frozenset({"true", "1", "yes"})
_RATE_LIMIT_WINDOW = timedelta(hours=1)
_RATE_LIMIT_MAX = 10

# In-memory state. Reset via ``_reset_state_for_tests`` in unit tests.
_RATE_LIMITER: dict[str, list[datetime]] = {}
_RUNTIME_OVERRIDES: dict[str, bool] = {}
_LOCK = threading.Lock()


# -------------------- Public API --------------------


def is_enabled(flag_name: str, default: bool = False) -> bool:
    """Return True if ``flag_name`` is enabled.

    Resolution order: env var > runtime override > YAML > ``default``.
    """
    env_value = _read_env(flag_name)
    if env_value is not None:
        return env_value

    with _LOCK:
        if flag_name in _RUNTIME_OVERRIDES:
            return _RUNTIME_OVERRIDES[flag_name]

    yaml_value = _read_yaml(flag_name)
    if yaml_value is not None:
        return yaml_value

    return default


def set_flag_runtime(
    flag_name: str,
    enabled: bool,
    reason: str,
    actor_token: str,
    source_ip: str,
) -> dict[str, Any]:
    """Apply a runtime flag override and persist an audit row.

    Returns a summary dict with ``flag_name``, ``enabled``, ``applied_at``.
    The caller is responsible for rate-limit enforcement (see
    :func:`_check_rate_limit`).
    """
    old_value = is_enabled(flag_name, default=False)
    with _LOCK:
        _RUNTIME_OVERRIDES[flag_name] = enabled

    applied_at = datetime.now(timezone.utc).isoformat()
    actor_hash = hashlib.sha256(actor_token.encode("utf-8")).hexdigest()
    _write_audit_row(
        flag_name=flag_name,
        old_value=_bool_to_str(old_value),
        new_value=_bool_to_str(enabled),
        reason=reason,
        actor_token_hash=actor_hash,
        source_ip=source_ip,
        timestamp=applied_at,
    )
    return {
        "flag_name": flag_name,
        "enabled": enabled,
        "applied_at": applied_at,
    }


def hash_actor_token(token: str) -> str:
    """Return the SHA256 hex digest used in audit rows."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# -------------------- Rate limiter --------------------


def _check_rate_limit(actor_token_hash: str) -> bool:
    """Return True if under the per-actor hourly quota, False otherwise.

    Records the current timestamp on success. Evicts timestamps older than
    the one-hour window before comparing against ``_RATE_LIMIT_MAX``.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - _RATE_LIMIT_WINDOW
    with _LOCK:
        history = [ts for ts in _RATE_LIMITER.get(actor_token_hash, []) if ts > cutoff]
        if len(history) >= _RATE_LIMIT_MAX:
            _RATE_LIMITER[actor_token_hash] = history
            return False
        history.append(now)
        _RATE_LIMITER[actor_token_hash] = history
        return True


# -------------------- Internals --------------------


def _read_env(flag_name: str) -> bool | None:
    """Return env-var value for ``FEATURE_<NAME>``, or None if unset."""
    raw = os.environ.get(f"FEATURE_{flag_name.upper()}")
    if raw is None:
        return None
    return raw.strip().lower() in _TRUTHY


def _read_yaml(flag_name: str) -> bool | None:
    """Return the YAML value for ``flag_name``, or None if absent/invalid."""
    try:
        text = _YAML_PATH.read_text()
    except FileNotFoundError:
        return None
    except OSError:
        logger.warning("Could not read feature flag YAML at %s", _YAML_PATH)
        return None
    try:
        data = yaml.safe_load(text) or {}
    except yaml.YAMLError:
        logger.warning("Invalid YAML in feature flag file %s", _YAML_PATH)
        return None
    if not isinstance(data, dict):
        return None
    value = data.get(flag_name)
    if isinstance(value, bool):
        return value
    return None


def _bool_to_str(value: bool) -> str:
    return "true" if value else "false"


def _write_audit_row(
    *,
    flag_name: str,
    old_value: str,
    new_value: str,
    reason: str,
    actor_token_hash: str,
    source_ip: str,
    timestamp: str,
) -> None:
    """Write a single audit row using the project's sqlite database."""
    db_url = get_settings().database_url
    db_path = _sqlite_path_from_url(db_url)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO feature_flag_audit "
            "(flag_name, old_value, new_value, reason, actor_token_hash, "
            "source_ip, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                flag_name, old_value, new_value, reason,
                actor_token_hash, source_ip, timestamp,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _sqlite_path_from_url(db_url: str) -> str:
    """Extract the filesystem path from a ``sqlite+aiosqlite:///...`` URL."""
    marker = ":///"
    idx = db_url.find(marker)
    if idx == -1:
        return db_url
    return db_url[idx + len(marker):]


def _reset_state_for_tests() -> None:
    """Clear in-memory overrides and rate-limit counters. Test-only."""
    with _LOCK:
        _RATE_LIMITER.clear()
        _RUNTIME_OVERRIDES.clear()
