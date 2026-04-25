"""sqlite3 query-count harness for the T13.90 N+1 audit.

Wraps :func:`sqlite3.connect` so that every connection produced inside
the ``count_queries`` block installs a ``set_trace_callback`` that
records each executed statement to a list. Call sites in production
code typically open short-lived connections (open / execute / close),
so a per-connection callback is enough — there is no shared connection
pool to instrument.

Usage::

    from tests._query_counter import count_queries

    with count_queries() as counter:
        client.get("/api/job-applications?...")

    assert len(counter.queries) <= 4

The harness is deliberately minimal:

* ``queries`` is a flat list of every statement string seen, in order.
* ``count_for(prefix)`` is a small filter for "count only SELECTs" or
  "count only INSERTs into a particular table" — useful when chatty
  PRAGMA statements run on every ``_connect`` call.
* The harness ignores ``sqlite_master`` introspection and
  ``PRAGMA foreign_keys`` because they are infrastructure noise that
  should not count toward an N+1 verdict.

The counter is **not thread-safe** — tests run synchronously through
the FastAPI ``TestClient`` and each request runs to completion before
the next assertion.
"""

from __future__ import annotations

import contextlib
import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass, field

# Statements that are pure infrastructure noise and should not influence
# the N+1 verdict. Trace strings are matched case-insensitively after
# stripping leading whitespace.
_NOISE_PREFIXES: tuple[str, ...] = (
    "pragma foreign_keys",
    "begin",
    "commit",
    "rollback",
    "select * from sqlite_master",
    "select name from sqlite_master",
)


def _is_noise(stmt: str) -> bool:
    """Return True for infrastructure statements we exclude from counts."""
    head = stmt.strip().lower()
    return any(head.startswith(p) for p in _NOISE_PREFIXES)


@dataclass
class QueryCounter:
    """Mutable container of statements seen during a counted block."""

    queries: list[str] = field(default_factory=list)

    def record(self, stmt: str) -> None:
        """Append a non-noise statement to the trace."""
        if not _is_noise(stmt):
            self.queries.append(stmt)

    def count_for(self, *prefixes: str) -> int:
        """Return how many recorded statements start with any prefix."""
        lowered = tuple(p.lower() for p in prefixes)
        return sum(
            1
            for q in self.queries
            if q.strip().lower().startswith(lowered)
        )

    def selects(self) -> int:
        """Convenience: count only SELECT statements."""
        return self.count_for("select")

    def reset(self) -> None:
        """Drop the recorded trace; useful between sub-phases of a test."""
        self.queries.clear()


@contextlib.contextmanager
def count_queries() -> Iterator[QueryCounter]:
    """Wrap ``sqlite3.connect`` to record every statement to the counter.

    The wrapper preserves the original ``sqlite3.connect`` callable on
    enter and restores it on exit, so nested ``with`` blocks degrade to
    independent counters (the inner block sees only its own queries
    because each connection's ``set_trace_callback`` writes to the
    counter that was current when the connection was created).

    The wrapper does NOT attempt to instrument ``sqlite3.Connection``
    instances created by ``aiosqlite`` or by SQLAlchemy — those go
    through ``sqlite3.connect`` indirectly via the standard library, so
    they are caught automatically. SQLAlchemy's connection pool may
    keep a connection open across requests; the callback persists for
    the lifetime of that connection, which is what we want.
    """
    counter = QueryCounter()
    original_connect = sqlite3.connect

    def wrapped(*args: object, **kwargs: object) -> sqlite3.Connection:
        conn = original_connect(*args, **kwargs)  # type: ignore[arg-type]
        conn.set_trace_callback(counter.record)
        return conn

    sqlite3.connect = wrapped  # type: ignore[assignment]
    try:
        yield counter
    finally:
        sqlite3.connect = original_connect  # type: ignore[assignment]


__all__ = ["QueryCounter", "count_queries"]
