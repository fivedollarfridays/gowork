"""Race + boundary tests for ``app.core.rate_limit.RateLimiter`` (T13.60).

These tests target three classes of bug that the existing
``test_rate_limit.py`` does not cover:

1. **Boundary off-by-one** — ensure exactly ``N`` requests are allowed
   and the ``N+1``-th is denied. The current limiter uses ``>=`` to
   compare ``len(timestamps)`` with ``self._max``; the test below pins
   that decision so a future refactor cannot silently flip it to ``>``.

2. **Concurrent over-allow** — fire ``2 * N`` threads simultaneously
   against a single key. The check-then-append in ``RateLimiter.check``
   is *not* protected by a lock; if a regression introduces real
   parallelism (e.g. removing the GIL or moving the limiter to a
   shared-memory backend without a lock) this test will surface it.
   Under CPython 3.14 with the GIL, the dict/list operations are
   coarsely serialized, but we still assert "exactly N allowed"
   to lock in the behaviour the production code promises callers.

3. **Window-reset semantics** — verify the sliding-window cutoff is
   ``timestamp > cutoff`` (strictly greater than ``now - window``),
   that resets are honoured exactly when the oldest timestamp ages
   out, and that per-key isolation holds across a reset.

The limiter reads time via :func:`time.monotonic`, so we patch
``app.core.rate_limit.time`` rather than using the
:mod:`backend.tests._fake_clock` ``datetime`` harness — the harness
does not affect the monotonic clock. This matches the existing
``test_window_expiry`` pattern in ``test_rate_limit.py``.
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from unittest.mock import patch

from app.core.rate_limit import RateLimiter

# A small, prime-ish limit makes assertions sharp: 3 allowed, 4th denied,
# and concurrent 2*N=6 threads must split exactly 3/3.
_LIMIT = 3
_WINDOW = 10


@contextmanager
def _patched_monotonic(initial: float = 1_000.0):
    """Replace ``app.core.rate_limit.time`` with a controllable fake.

    Yields a callable ``advance(seconds)`` so individual tests can
    drive the monotonic clock forward without leaking real time
    dependence into the assertion.
    """
    state = {"now": initial}

    class _FakeTime:
        @staticmethod
        def monotonic() -> float:
            return state["now"]

    def advance(seconds: float) -> None:
        state["now"] += seconds

    with patch("app.core.rate_limit.time", _FakeTime):
        yield advance


def _fresh_limiter() -> RateLimiter:
    return RateLimiter(max_requests=_LIMIT, window_seconds=_WINDOW)


# --------------------------------------------------------------------- #
# Test 1: under-limit — all allowed.
# --------------------------------------------------------------------- #


def test_under_limit_all_allowed() -> None:
    """N sequential requests against a single key are all allowed."""
    limiter = _fresh_limiter()
    results = [limiter.check("ip-a") for _ in range(_LIMIT)]
    assert results == [True] * _LIMIT


# --------------------------------------------------------------------- #
# Test 2: over-limit — exactly N allowed, the N+1-th denied.
# --------------------------------------------------------------------- #


def test_over_limit_excess_denied() -> None:
    """N+1 sequential requests: first N allowed, last denied."""
    limiter = _fresh_limiter()
    results = [limiter.check("ip-a") for _ in range(_LIMIT + 1)]
    # Exactly _LIMIT True followed by one False.
    assert results == [True] * _LIMIT + [False]
    # Verify the recorded timestamp count matches what was admitted.
    assert len(limiter._requests["ip-a"]) == _LIMIT


# --------------------------------------------------------------------- #
# Test 3: concurrent at the boundary — no over-allow under burst.
# --------------------------------------------------------------------- #


def test_concurrent_at_boundary_no_over_allow() -> None:
    """2*N threads race against a single key; exactly N succeed.

    The barrier ensures all threads are released simultaneously so the
    check-then-append window is exercised. Under correct semantics,
    *exactly* ``_LIMIT`` calls return True and the rest False — never
    more, never fewer.
    """
    limiter = _fresh_limiter()
    n_threads = _LIMIT * 2
    barrier = threading.Barrier(n_threads)

    def _attempt() -> bool:
        # Synchronize the "go" instant so all threads contend together.
        barrier.wait(timeout=5.0)
        return limiter.check("burst-key")

    with ThreadPoolExecutor(max_workers=n_threads) as pool:
        futures = [pool.submit(_attempt) for _ in range(n_threads)]
        outcomes = [f.result(timeout=5.0) for f in futures]

    allowed = sum(1 for ok in outcomes if ok)
    denied = sum(1 for ok in outcomes if not ok)

    # The whole point of the test: never over-allow under contention.
    assert allowed == _LIMIT, (
        f"over-allow detected: {allowed} allowed, expected exactly {_LIMIT}"
    )
    assert denied == n_threads - _LIMIT
    # Internal state should match: exactly _LIMIT recorded timestamps.
    assert len(limiter._requests["burst-key"]) == _LIMIT


# --------------------------------------------------------------------- #
# Test 4: window reset — N more allowed after the window passes.
# --------------------------------------------------------------------- #


def test_window_reset_after_period() -> None:
    """After the full window passes, a fresh batch of N is allowed."""
    with _patched_monotonic(initial=1_000.0) as advance:
        limiter = _fresh_limiter()
        # Saturate.
        for _ in range(_LIMIT):
            assert limiter.check("ip-a") is True
        assert limiter.check("ip-a") is False

        # Advance just past the window so every recorded timestamp
        # ages out of the cutoff (now - window).
        advance(_WINDOW + 1)

        post_reset = [limiter.check("ip-a") for _ in range(_LIMIT)]
        assert post_reset == [True] * _LIMIT
        # And the (N+1)-th is still denied in the new window.
        assert limiter.check("ip-a") is False


# --------------------------------------------------------------------- #
# Test 5: per-key isolation — one key saturated, another unaffected.
# --------------------------------------------------------------------- #


def test_per_key_isolation() -> None:
    """Saturating key A must not affect key B's quota."""
    limiter = _fresh_limiter()
    for _ in range(_LIMIT):
        assert limiter.check("key-A") is True
    assert limiter.check("key-A") is False

    # Key B is fresh — should get the full quota independently.
    for _ in range(_LIMIT):
        assert limiter.check("key-B") is True
    assert limiter.check("key-B") is False

    # Key A's denial state is unchanged.
    assert limiter.check("key-A") is False


def test_per_key_isolation_after_window_reset() -> None:
    """A's reset does not retroactively grant or deny B's quota.

    Timeline (with ``_WINDOW = 10``)::

        T = 2000   key-A saturates (3 timestamps at T=2000)
        T = 2001   key-B records 1 timestamp
        T = 2010   advance by _WINDOW - 1 = 9  →  now = 2010
                   cutoff for A = 2000   →  A's timestamps (== 2000)
                                            fail ``t > cutoff`` → expire
                   cutoff for B = 2000   →  B's timestamp (2001 > 2000)
                                            still live
                   so A has a full reset, B has _LIMIT - 1 slots left.
    """
    with _patched_monotonic(initial=2_000.0) as advance:
        limiter = _fresh_limiter()
        for _ in range(_LIMIT):
            limiter.check("key-A")
        # B uses one slot 1 tick after A is saturated.
        advance(1.0)
        assert limiter.check("key-B") is True

        # Advance so A's timestamps age out exactly, but B's survives.
        advance(_WINDOW - 1)
        # A may take the full quota again.
        for _ in range(_LIMIT):
            assert limiter.check("key-A") is True
        # B's surviving timestamp leaves only _LIMIT - 1 slots open,
        # NOT a full reset — that proves per-key isolation.
        b_remaining = [limiter.check("key-B") for _ in range(_LIMIT - 1)]
        assert b_remaining == [True] * (_LIMIT - 1)
        assert limiter.check("key-B") is False


# --------------------------------------------------------------------- #
# Test 6: window-boundary off-by-one — ``>`` cutoff comparison.
# --------------------------------------------------------------------- #


def test_window_boundary_strictly_greater_than_cutoff() -> None:
    """A timestamp exactly ``window`` old is treated as expired.

    The production code filters with ``t > cutoff`` where
    ``cutoff = now - window``. So a timestamp recorded at ``T`` is
    expired the instant ``now - window >= T``, i.e. when exactly
    ``window`` seconds have passed. This locks that decision in.
    """
    with _patched_monotonic(initial=5_000.0) as advance:
        limiter = _fresh_limiter()
        # Saturate at T=5000.
        for _ in range(_LIMIT):
            assert limiter.check("k") is True
        assert limiter.check("k") is False

        # Advance to *exactly* the window edge: now = 5000 + _WINDOW.
        # cutoff = now - _WINDOW = 5000, and the recorded timestamps
        # are all == 5000, which is NOT strictly greater than cutoff.
        # All three should expire and the next call should be allowed.
        advance(_WINDOW)
        assert limiter.check("k") is True


def test_window_boundary_one_tick_before_expiry() -> None:
    """One tick before the boundary, the oldest timestamp is still live."""
    with _patched_monotonic(initial=7_000.0) as advance:
        limiter = _fresh_limiter()
        for _ in range(_LIMIT):
            assert limiter.check("k") is True
        assert limiter.check("k") is False

        # Just shy of the window — every recorded timestamp is still
        # strictly greater than cutoff, so the limit must hold.
        advance(_WINDOW - 0.001)
        assert limiter.check("k") is False


# --------------------------------------------------------------------- #
# Test 7 (bonus): clear() is honoured even mid-window.
# --------------------------------------------------------------------- #


def test_clear_resets_mid_window() -> None:
    """``clear()`` drops in-flight timestamps regardless of window state."""
    with _patched_monotonic(initial=9_000.0):
        limiter = _fresh_limiter()
        for _ in range(_LIMIT):
            limiter.check("k")
        assert limiter.check("k") is False
        limiter.clear()
        # Full quota is available again immediately.
        for _ in range(_LIMIT):
            assert limiter.check("k") is True
