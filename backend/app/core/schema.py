"""Database schema — DDL and column allowlists for SQLite tables.

DEPRECATED: DDL_SQL is retained as a re-export for backward compatibility
only. New callers should use ``app.core.migrations.runner.apply_pending``
instead; the authoritative m001 DDL lives in
``app.core.migrations.m001_initial.DDL_SQL``.
"""

from app.core.migrations.m001_initial import DDL_SQL as _M001_DDL_SQL

# Backward-compatible re-export. Kept byte-for-byte via import from m001.
DDL_SQL = _M001_DDL_SQL

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
        "source", "scraped_at", "expires_at", "credit_check", "fair_chance",
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
    "share_tokens": {"token", "session_id", "created_at", "expires_at"},
}

JSON_FIELDS = {"services"}
