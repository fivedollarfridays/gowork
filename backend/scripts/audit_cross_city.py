"""Cross-city leakage audit — POST /api/assessment with all four ZIP scenarios.

Run from backend/:
    .venv/Scripts/python.exe -m scripts.audit_cross_city

Captures the full plan response to .tmp/audit/resp_<zip>_post_fix.json and
prints a leak summary (Alabama strings in TX response, Texas strings in AL).
Exits 1 if any cross-city leakage is detected. Useful as a smoke gate
before demos and after pipeline changes.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Default to fort-worth so the seed runs the FW data dir; we override
# city per-request via the per-request context var (driven by ZIP).
os.environ.setdefault("CITY", "fort-worth")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_audit.db")

# Force-reset DB so seed runs fresh.
db_path = Path("test_audit.db")
if db_path.exists():
    db_path.unlink()

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

OUT_DIR = Path(".tmp/audit")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ZIPS = [
    ("76102", "fort-worth"),
    ("76104", "fort-worth"),
    ("36104", "montgomery"),
    ("36101", "montgomery"),
]

PAYLOAD_BASE = {
    "employment_status": "unemployed",
    "barriers": {
        "transportation": True,
        "childcare": True,
        "criminal_record": True,
        "credit": False,
    },
    "work_history": "Warehouse worker for 3 years",
    "schedule_constraints": {"available_hours": "daytime"},
    "has_vehicle": False,
    "record_profile": {
        "record_types": ["misdemeanor"],
        "charge_categories": [],
        "years_since_conviction": 5,
        "completed_sentence": True,
    },
}

AL_LEAK_TOKENS = (
    "montgomery", "alabama", "mats", "the m,", "alabama dhr",
    "head start / early head start, montgomery",
    "family guidance center of alabama", "trenholm", "mrwtc",
    "salvation army, montgomery", "consumer credit counseling service of central alabama",
    "greenpath",
    # Note: 'ceap' is BOTH AL (Low-Income Home Energy Assistance) and TX
    # (Comprehensive Energy Assistance Program). Excluded to avoid false
    # positives — distinct AL strings above already catch real leaks.
)
TX_LEAK_TOKENS = (
    "fort worth", "tarrant", "trinity metro", "twc ", "lockheed", "alcon",
    "bnsf", "je dunn", "texas", "expunction", "nondisclosure",
    "workforce solutions", "jps health", "tarrant county college",
    "legal aid of northwest texas",
)


def find_leaks(text: str, tokens: tuple[str, ...]) -> list[str]:
    text_l = text.lower()
    return [t for t in tokens if t in text_l]


def main() -> int:
    # Use context-managed TestClient so lifespan startup (which runs init_db
    # and seed_database) actually executes.
    with TestClient(app) as client:
        return _run_audit(client)


def _run_audit(client) -> int:
    results = []
    for zip_code, expected_city in ZIPS:
        payload = {**PAYLOAD_BASE, "zip_code": zip_code}
        r = client.post("/api/assessment/", json=payload)
        out_path = OUT_DIR / f"resp_{zip_code}_post_fix.json"
        if r.status_code != 201:
            results.append((zip_code, expected_city, r.status_code, [], [], None))
            print(f"\n[{zip_code} -> {expected_city}] HTTP {r.status_code}")
            print(r.text[:500])
            continue
        body = r.json()
        out_path.write_text(json.dumps(body, indent=2, default=str))
        text = json.dumps(body, default=str)
        if expected_city == "fort-worth":
            leaks = find_leaks(text, AL_LEAK_TOKENS)
            ok = find_leaks(text, TX_LEAK_TOKENS)
        else:
            leaks = find_leaks(text, TX_LEAK_TOKENS)
            ok = find_leaks(text, AL_LEAK_TOKENS)
        plan = body.get("plan", {})
        results.append((
            zip_code, expected_city, r.status_code, leaks, ok,
            (
                len(plan.get("barriers", [])),
                len(plan.get("strong_matches", [])) + len(plan.get("after_repair", [])),
                sum(len(b.get("resources", [])) for b in plan.get("barriers", [])),
            ),
        ))
        print(f"\n[{zip_code} -> {expected_city}] HTTP 201")
        print(f"  Wrong-city leaks: {leaks}")
        print(f"  Right-city tokens present: {ok[:6]}...")
        print(f"  Barriers: {len(plan.get('barriers', []))}, "
              f"Jobs: {len(plan.get('strong_matches', [])) + len(plan.get('after_repair', []))}, "
              f"Resources total: {sum(len(b.get('resources', [])) for b in plan.get('barriers', []))}")
        print(f"  Immediate next steps:")
        for s in plan.get("immediate_next_steps", []):
            print(f"   - {s}")
    print("\n=== SUMMARY ===")
    for zip_code, expected, status, leaks, ok, counts in results:
        print(f"  {zip_code} -> {expected}: HTTP {status}, leaks={len(leaks)}, "
              f"counts(barriers/jobs/resources)={counts}")
    bad = [r for r in results if r[3]]
    if bad:
        print(f"\nFAIL: {len(bad)} responses contained wrong-city tokens.")
        return 1
    print("\nPASS: zero cross-city leakage detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
