"""In-process pub/sub event bus (T12.7).

Lightweight synchronous dispatcher for decoupling domain writers from
side-effect consumers (e.g. the outcomes listener in S12a). Handlers
register against string event names; `emit()` dispatches to every
registered handler in subscription order. Exceptions inside one handler
are logged and swallowed so a single broken listener cannot break the
emit call or block sibling listeners.

Thread-safe via a module-level lock around the subscribers dict. Dispatch
itself runs outside the lock (against a snapshot) so handlers can freely
emit or subscribe without deadlocking. Async dispatch is an optional
follow-up — S12a subscribers are all cheap synchronous SQLite writes.
"""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from typing import Callable

logger = logging.getLogger(__name__)

EventHandler = Callable[[dict], None]

_subscribers: dict[str, list[EventHandler]] = defaultdict(list)
_lock = threading.Lock()


def subscribe(event_name: str, handler: EventHandler) -> None:
    """Register `handler` for `event_name`. Re-subscribing is a no-op.

    Idempotency lets callers register listeners at module import or
    startup without worrying about duplicate delivery.
    """
    with _lock:
        handlers = _subscribers[event_name]
        if handler not in handlers:
            handlers.append(handler)


def unsubscribe(event_name: str, handler: EventHandler) -> None:
    """Remove `handler` from `event_name`'s list. Silent if absent.

    Primarily used by tests for per-test cleanup; production code
    typically registers once at startup.
    """
    with _lock:
        handlers = _subscribers.get(event_name)
        if not handlers:
            return
        try:
            handlers.remove(handler)
        except ValueError:
            pass


def emit(event_name: str, payload: dict) -> None:
    """Dispatch `payload` to every handler registered for `event_name`.

    Dispatch is synchronous and ordered by subscription. Handler
    exceptions are logged at ERROR and suppressed — one broken listener
    can't block emission. Returns nothing; emit is fire-and-forget.
    """
    # Snapshot under the lock so adding/removing handlers during
    # dispatch doesn't mutate our iteration target.
    with _lock:
        handlers = list(_subscribers.get(event_name, ()))
    for handler in handlers:
        try:
            handler(payload)
        except Exception:  # noqa: BLE001 — isolate handler failures
            logger.exception(
                "Handler %r failed for event %r", handler, event_name,
            )


def clear_all_subscribers() -> None:
    """Wipe every registered handler. Test-only utility."""
    with _lock:
        _subscribers.clear()


__all__ = [
    "EventHandler",
    "clear_all_subscribers",
    "emit",
    "subscribe",
    "unsubscribe",
]
