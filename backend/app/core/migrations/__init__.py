"""Migration infrastructure for the MontGoWork backend SQLite database.

Pattern mirrors ops:lib/db.py + ops:lib/migrations/: each migration is a
Python module named m{NNN}_*.py exporting SCHEMA_VERSION, upgrade(conn),
and downgrade(conn). The runner discovers them by glob + sort.
"""

from app.core.migrations import runner

__all__ = ["runner"]
