"""Outcome tracker -- records and retrieves outcome signals.

Stores outcome records keyed by session_id (upsert semantics).
Thread-safe for single-process use (SQLite + GIL).

This is the WRITE side of the N+1 intelligence loop.
The aggregator module is the READ side.
"""

from app.modules.outcomes.types import OutcomeRecord


class OutcomeTracker:
    """In-memory outcome storage with city-aware retrieval.

    In production, this would be backed by a database table.
    The in-memory implementation enables fast testing and
    zero-dependency operation for the hackathon demo.
    """

    def __init__(self) -> None:
        self._records: dict[str, OutcomeRecord] = {}

    def record_outcome(self, record: OutcomeRecord) -> None:
        """Store an outcome record. Replaces existing record for same session."""
        self._records[record.session_id] = record

    def count(self) -> int:
        """Total outcome records stored."""
        return len(self._records)

    def get_outcomes_for_city(self, city: str) -> list[OutcomeRecord]:
        """Retrieve all outcomes for a specific city."""
        return [r for r in self._records.values() if r.city == city]

    def get_all_outcomes(self) -> list[OutcomeRecord]:
        """Retrieve all stored outcomes across all cities."""
        return list(self._records.values())
