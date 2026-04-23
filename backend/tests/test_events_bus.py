"""Tests for the in-process pub/sub event bus (T12.7).

Covers synchronous dispatch, idempotent subscription, handler isolation
(one broken listener cannot block others), unsubscribe, and basic
thread-safety of concurrent subscribe+emit.

Each test clears subscribers before running so tests don't interact.
"""

from __future__ import annotations

import logging
import threading

import pytest

from app.core import events


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _clear_subscribers() -> None:
    """Reset the global subscriber registry between tests."""
    events.clear_all_subscribers()
    yield
    events.clear_all_subscribers()


# -------------------- Dispatch --------------------


def test_emit_dispatches_to_subscribers() -> None:
    received: list[dict] = []
    events.subscribe("x.created", received.append)

    events.emit("x.created", {"id": 1})

    assert received == [{"id": 1}]


def test_multiple_subscribers_all_called() -> None:
    a: list[dict] = []
    b: list[dict] = []
    events.subscribe("x.updated", a.append)
    events.subscribe("x.updated", b.append)

    events.emit("x.updated", {"v": 7})

    assert a == [{"v": 7}]
    assert b == [{"v": 7}]


def test_emit_unknown_event_is_silent() -> None:
    # No subscribers → no exception, no side effects.
    events.emit("never.registered", {"k": "v"})


# -------------------- Idempotent subscribe --------------------


def test_subscribe_is_idempotent() -> None:
    calls: list[dict] = []

    def handler(payload: dict) -> None:
        calls.append(payload)

    events.subscribe("x.created", handler)
    events.subscribe("x.created", handler)  # no-op

    events.emit("x.created", {"n": 1})

    assert calls == [{"n": 1}]


# -------------------- Unsubscribe --------------------


def test_unsubscribe_removes_handler() -> None:
    calls: list[dict] = []

    def handler(payload: dict) -> None:
        calls.append(payload)

    events.subscribe("x.created", handler)
    events.unsubscribe("x.created", handler)

    events.emit("x.created", {"n": 1})

    assert calls == []


def test_unsubscribe_unknown_handler_is_silent() -> None:
    def handler(_: dict) -> None: ...

    # Never subscribed — must not raise.
    events.unsubscribe("x.created", handler)


# -------------------- Handler isolation --------------------


def test_handler_exception_does_not_block_other_handlers(
    caplog: pytest.LogCaptureFixture,
) -> None:
    good_calls: list[dict] = []

    def bad(_: dict) -> None:
        raise RuntimeError("boom")

    def good(payload: dict) -> None:
        good_calls.append(payload)

    events.subscribe("x.created", bad)
    events.subscribe("x.created", good)

    with caplog.at_level(logging.ERROR, logger="app.core.events"):
        events.emit("x.created", {"n": 42})

    assert good_calls == [{"n": 42}]
    # logger.exception() appends the traceback under exc_info; caplog.text
    # renders the full formatted record including the traceback string.
    assert "RuntimeError" in caplog.text
    assert "boom" in caplog.text


# -------------------- Thread safety --------------------


def test_thread_safety_concurrent_subscribe_and_emit() -> None:
    """Many threads subscribing + emitting must not corrupt state."""
    counter = {"n": 0}
    counter_lock = threading.Lock()

    def handler(_: dict) -> None:
        with counter_lock:
            counter["n"] += 1

    def subscribe_n_times() -> None:
        # Subscribe the same handler 50× → idempotent, so only 1 effective.
        for _ in range(50):
            events.subscribe("race", handler)

    def emit_n_times() -> None:
        for _ in range(50):
            events.emit("race", {"x": 1})

    threads = [threading.Thread(target=subscribe_n_times) for _ in range(4)]
    threads += [threading.Thread(target=emit_n_times) for _ in range(4)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Subscribe is idempotent so only one handler is active. Emits across
    # threads each run the single handler once → 4 threads × 50 emits.
    # Some emits may have happened before the first subscribe completed,
    # so the only invariant we assert is: counter did not exceed the
    # maximum (4 × 50 = 200) and registry has exactly one handler.
    assert counter["n"] <= 200
    with events._lock:  # type: ignore[attr-defined]  # private OK in test
        assert len(events._subscribers["race"]) == 1  # type: ignore[attr-defined]


# -------------------- clear_all_subscribers --------------------


def test_clear_all_subscribers_resets_registry() -> None:
    calls: list[dict] = []
    events.subscribe("x.created", calls.append)

    events.clear_all_subscribers()
    events.emit("x.created", {"n": 1})

    assert calls == []
