"""Migration 001 — initial schema: extracted verbatim from app.core.schema.DDL_SQL.

The DDL string below must remain byte-for-byte identical to the original
DDL_SQL blob in app/core/schema.py. Downstream S12 migrations (m002+) layer
new tables on top of this baseline.
"""

import sqlite3

SCHEMA_VERSION = 1

DDL_SQL = """
CREATE TABLE IF NOT EXISTS employers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    lat REAL,
    lng REAL,
    license_type TEXT,
    industry TEXT,
    active INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS transit_routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_number INTEGER NOT NULL,
    route_name TEXT NOT NULL,
    weekday_start TEXT,
    weekday_end TEXT,
    saturday INTEGER DEFAULT 1,
    sunday INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS transit_stops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER REFERENCES transit_routes(id),
    stop_name TEXT NOT NULL,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    sequence INTEGER
);
CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    address TEXT,
    lat REAL,
    lng REAL,
    phone TEXT,
    url TEXT,
    eligibility TEXT,
    services TEXT,
    hours TEXT,
    notes TEXT,
    health_status TEXT DEFAULT 'healthy'
);
CREATE TABLE IF NOT EXISTS job_listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    description TEXT,
    url TEXT,
    source TEXT,
    scraped_at TEXT NOT NULL,
    expires_at TEXT,
    credit_check TEXT DEFAULT 'unknown',
    fair_chance INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    barriers TEXT NOT NULL,
    credit_profile TEXT,
    qualifications TEXT,
    plan TEXT,
    profile TEXT,
    benefits_profile TEXT,
    action_checklist TEXT,
    previous_plan TEXT,
    expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS feedback_tokens (
    token TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS visit_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    submitted_at TEXT NOT NULL,
    made_it_to_center INTEGER NOT NULL,
    outcomes TEXT,
    plan_accuracy INTEGER NOT NULL,
    free_text TEXT,
    reviewed INTEGER DEFAULT 0,
    action_taken TEXT
);
CREATE TABLE IF NOT EXISTS resource_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id INTEGER REFERENCES resources(id),
    session_id TEXT NOT NULL,
    helpful INTEGER NOT NULL,
    barrier_type TEXT,
    submitted_at TEXT NOT NULL,
    UNIQUE(resource_id, session_id)
);
CREATE TABLE IF NOT EXISTS barriers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    playbook TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS barrier_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_barrier_id TEXT NOT NULL REFERENCES barriers(id),
    target_barrier_id TEXT NOT NULL REFERENCES barriers(id),
    relationship_type TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    UNIQUE(source_barrier_id, target_barrier_id, relationship_type)
);
CREATE TABLE IF NOT EXISTS barrier_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrier_id TEXT NOT NULL REFERENCES barriers(id),
    resource_id INTEGER NOT NULL,
    impact_strength REAL NOT NULL,
    notes TEXT,
    UNIQUE(barrier_id, resource_id)
);
CREATE TABLE IF NOT EXISTS employer_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employer_name TEXT NOT NULL UNIQUE,
    fair_chance INTEGER DEFAULT 0,
    excluded_charges TEXT DEFAULT '[]',
    lookback_years INTEGER,
    bg_check_timing TEXT DEFAULT 'pre_offer',
    industry TEXT,
    source TEXT,
    montgomery_area INTEGER DEFAULT 1  -- TODO(s7): rename to service_area when migration tooling is ready
);
CREATE TABLE IF NOT EXISTS record_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    record_types TEXT DEFAULT '[]',
    charge_categories TEXT DEFAULT '[]',
    years_since_conviction INTEGER,
    completed_sentence INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS share_tokens (
    token TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
"""

# Tables created by DDL_SQL, in dependency-safe reverse order for downgrade.
# Children (referencing FKs) dropped before parents.
_DOWNGRADE_ORDER = (
    "share_tokens",
    "record_profiles",
    "employer_policies",
    "barrier_resources",
    "barrier_relationships",
    "barriers",
    "resource_feedback",
    "visit_feedback",
    "feedback_tokens",
    "sessions",
    "job_listings",
    "resources",
    "transit_stops",
    "transit_routes",
    "employers",
)


def upgrade(conn: sqlite3.Connection) -> None:
    """Apply migration 001 — idempotent CREATE TABLE IF NOT EXISTS batch."""
    conn.executescript(DDL_SQL)


def downgrade(conn: sqlite3.Connection) -> None:
    """Drop all tables created by migration 001, in reverse-dependency order."""
    for table in _DOWNGRADE_ORDER:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
