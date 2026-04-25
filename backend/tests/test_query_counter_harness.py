"""Smoke tests for the T13.90 query-count harness (`_query_counter.py`).

The N+1 audit's verdict rests entirely on the harness counting the
right thing — this file pins the bare-minimum behaviours so a future
refactor cannot silently mask an N+1 by under-counting.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from tests._query_counter import QueryCounter, count_queries


@pytest.fixture
def db_file(tmp_path: Path) -> str:
    db = str(tmp_path / "harness.db")
    conn = sqlite3.connect(db)
    try:
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
        conn.executemany(
            "INSERT INTO t (id, v) VALUES (?, ?)",
            [(i, f"row-{i}") for i in range(1, 6)],
        )
        conn.commit()
    finally:
        conn.close()
    return db


def test_counter_records_select(db_file: str) -> None:
    """A SELECT inside the block lands in `counter.queries`."""
    with count_queries() as counter:
        conn = sqlite3.connect(db_file)
        try:
            conn.execute("SELECT id FROM t WHERE id = ?", (1,)).fetchall()
        finally:
            conn.close()
    assert counter.selects() == 1
    assert any("SELECT id FROM t" in q for q in counter.queries)


def test_counter_strips_noise_pragmas(db_file: str) -> None:
    """``PRAGMA foreign_keys`` and BEGIN/COMMIT do not pollute the count."""
    with count_queries() as counter:
        conn = sqlite3.connect(db_file)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("BEGIN")
            conn.execute("INSERT INTO t (id, v) VALUES (?, ?)", (99, "x"))
            conn.execute("COMMIT")
        finally:
            conn.close()
    # Only the INSERT should be counted; PRAGMA + BEGIN + COMMIT noise.
    assert counter.count_for("insert") == 1
    assert counter.count_for("pragma") == 0


def test_counter_n_plus_one_signature(db_file: str) -> None:
    """A simulated N+1 produces query count == 1 + N."""
    with count_queries() as counter:
        conn = sqlite3.connect(db_file)
        try:
            ids = [
                r[0]
                for r in conn.execute("SELECT id FROM t ORDER BY id").fetchall()
            ]
            for rid in ids:
                conn.execute(
                    "SELECT v FROM t WHERE id = ?", (rid,),
                ).fetchall()
        finally:
            conn.close()
    # 5 rows + 1 list query = 6 SELECTs.
    assert counter.selects() == 1 + len(ids)


def test_counter_constant_signature(db_file: str) -> None:
    """A batched ``WHERE id IN (...)`` shows up as exactly 1 SELECT."""
    with count_queries() as counter:
        conn = sqlite3.connect(db_file)
        try:
            ids = [1, 2, 3, 4, 5]
            placeholders = ", ".join("?" for _ in ids)
            conn.execute(
                f"SELECT id, v FROM t WHERE id IN ({placeholders})",
                ids,
            ).fetchall()
        finally:
            conn.close()
    assert counter.selects() == 1


def test_counter_restores_sqlite_connect_on_exit(db_file: str) -> None:
    """``count_queries`` must not leak the wrapper into other tests."""
    original = sqlite3.connect
    with count_queries():
        assert sqlite3.connect is not original
    assert sqlite3.connect is original


def test_counter_reset_drops_history() -> None:
    """`QueryCounter.reset()` clears recorded statements."""
    counter = QueryCounter()
    counter.record("SELECT 1")
    counter.record("SELECT 2")
    assert counter.selects() == 2
    counter.reset()
    assert counter.selects() == 0
