"""add_barrier_graph_tables

Revision ID: 8ae7be7d93ea
Revises: 
Create Date: 2026-03-07 14:44:39.395076

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ae7be7d93ea'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create barrier graph tables."""
    op.execute("""
    CREATE TABLE IF NOT EXISTS barriers (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        playbook TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    op.execute("""
    CREATE TABLE IF NOT EXISTS barrier_relationships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_barrier_id TEXT NOT NULL REFERENCES barriers(id),
        target_barrier_id TEXT NOT NULL REFERENCES barriers(id),
        relationship_type TEXT NOT NULL,
        weight REAL DEFAULT 1.0,
        UNIQUE(source_barrier_id, target_barrier_id, relationship_type)
    )
    """)
    op.execute("""
    CREATE TABLE IF NOT EXISTS barrier_resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrier_id TEXT NOT NULL REFERENCES barriers(id),
        resource_id INTEGER NOT NULL,
        impact_strength REAL NOT NULL,
        notes TEXT,
        UNIQUE(barrier_id, resource_id)
    )
    """)


def downgrade() -> None:
    """Drop barrier graph tables."""
    op.drop_table("barrier_resources")
    op.drop_table("barrier_relationships")
    op.drop_table("barriers")
