"""Database schema — DDL and column allowlists for SQLite tables."""

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
    credit_check TEXT DEFAULT 'unknown'
);
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    barriers TEXT NOT NULL,
    credit_profile TEXT,
    qualifications TEXT,
    plan TEXT,
    profile TEXT,
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
    montgomery_area INTEGER DEFAULT 1
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
"""

ALLOWED_COLUMNS = {
    "employers": {"name", "address", "lat", "lng", "license_type", "industry", "active"},
    "transit_routes": {"route_number", "route_name", "weekday_start", "weekday_end", "saturday", "sunday"},
    "resources": {
        "name", "category", "subcategory", "address", "lat", "lng",
        "phone", "url", "eligibility", "services", "hours", "notes",
    },
    "transit_stops": {"route_id", "stop_name", "lat", "lng", "sequence"},
    "job_listings": {
        "title", "company", "location", "description", "url",
        "source", "scraped_at", "expires_at", "credit_check",
    },
    "barriers": {"id", "name", "category", "description", "playbook"},
    "barrier_relationships": {
        "source_barrier_id", "target_barrier_id", "relationship_type", "weight",
    },
    "barrier_resources": {"barrier_id", "resource_id", "impact_strength", "notes"},
    "employer_policies": {
        "employer_name", "fair_chance", "excluded_charges",
        "lookback_years", "bg_check_timing", "industry",
        "source", "montgomery_area",
    },
    "record_profiles": {
        "session_id", "record_types", "charge_categories",
        "years_since_conviction", "completed_sentence",
    },
}

JSON_FIELDS = {"services"}
