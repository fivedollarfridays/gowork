"""Load and normalize BrightData pre-built job datasets.

Parses JSON, JSONL, or CSV files containing structured job records from
BrightData's pre-built datasets. Embeds salary data into description text
so the existing PVS salary_parser can extract it without pipeline changes.
"""

import csv
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries_jobs import insert_job_listings
from app.integrations.brightdata.cache import (
    FIELD_LIMITS,
    get_existing_urls,
    should_exclude,
    truncate,
)
from app.integrations.brightdata.salary_embed import embed_salary_text, is_high_salary
from app.integrations.brightdata.types import BrightDataJobRecord


def _get(record: dict, *keys: str) -> str | None:
    """Return first non-empty string value from record."""
    for k in keys:
        v = record.get(k)
        if v:
            return str(v).strip()
    return None


def _build_location(record: dict) -> str | None:
    """Build location string from various field formats."""
    loc = _get(record, "location")
    if loc:
        return loc
    city = _get(record, "city")
    state = _get(record, "state")
    if city and state:
        return f"{city}, {state}"
    return city or state


def normalize_dataset_record(record: dict) -> BrightDataJobRecord | None:
    """Normalize a raw BrightData dataset record to BrightDataJobRecord.

    Returns None if the record should be skipped (no title, executive, high salary).
    """
    title = _get(record, "title", "job_title", "name")
    if not title:
        return None

    normalized = {**record, "title": title}
    if should_exclude(normalized):
        return None

    salary = _get(record, "salary", "salary_range", "compensation")
    if is_high_salary(salary):
        return None
    description = _get(record, "description", "job_description") or ""
    description = embed_salary_text(description, salary)

    return BrightDataJobRecord(
        title=truncate(title, FIELD_LIMITS["title"]),
        company=truncate(
            _get(record, "company", "company_name", "employer"),
            FIELD_LIMITS["company"],
        ),
        location=truncate(_build_location(record), FIELD_LIMITS["location"]),
        description=truncate(description, FIELD_LIMITS["description"]),
        url=truncate(_get(record, "url", "apply_link", "apply_url"), FIELD_LIMITS["url"]),
    )


def _parse_json(path: Path) -> list[dict]:
    """Parse a JSON array file."""
    with open(path) as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]


def _parse_jsonl(path: Path) -> list[dict]:
    """Parse a JSONL file (one JSON object per line)."""
    records: list[dict] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _parse_csv(path: Path) -> list[dict]:
    """Parse a CSV file with header row."""
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _dedup_key(record: BrightDataJobRecord) -> str:
    """Dedup key: lowercase (title, company)."""
    title = (record.title or "").lower().strip()
    company = (record.company or "").lower().strip()
    return f"{title}||{company}"


def _is_montgomery_area(location: str | None) -> bool:
    """Check if location is in the Montgomery, AL area."""
    if not location:
        return False
    loc_lower = location.lower()
    if "montgomery" in loc_lower:
        return True
    zip_match = re.search(r"\b(360\d{2}|361\d{2})\b", location)
    return zip_match is not None


def parse_dataset_file(
    path: Path,
    *,
    montgomery_only: bool = False,
) -> list[BrightDataJobRecord]:
    """Parse a BrightData dataset file and return normalized records.

    Supports JSON (array), JSONL, and CSV formats.
    Deduplicates by (title, company) pair.
    Optionally filters to Montgomery-area jobs only.
    """
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        raw = _parse_jsonl(path)
    elif suffix == ".csv":
        raw = _parse_csv(path)
    else:
        raw = _parse_json(path)

    seen: set[str] = set()
    results: list[BrightDataJobRecord] = []
    for record in raw:
        normalized = normalize_dataset_record(record)
        if normalized is None:
            continue
        key = _dedup_key(normalized)
        if key in seen:
            continue
        if montgomery_only and not _is_montgomery_area(normalized.location):
            continue
        seen.add(key)
        results.append(normalized)
    return results


async def store_dataset_records(
    session: AsyncSession,
    records: list[BrightDataJobRecord],
) -> int:
    """Deduplicate by URL and insert dataset records into job_listings.

    Returns count of newly inserted records.
    """
    if not records:
        return 0

    incoming_urls = [r.url for r in records if r.url]
    existing_urls = await get_existing_urls(session, incoming_urls)

    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    expires = (now_dt + timedelta(days=90)).isoformat()

    listings = []
    for record in records:
        if record.url and record.url in existing_urls:
            continue
        listings.append({
            "title": record.title,
            "company": record.company,
            "location": record.location,
            "description": record.description,
            "url": record.url,
            "source": "brightdata:dataset",
            "scraped_at": now,
            "expires_at": expires,
        })

    return await insert_job_listings(session, listings)
