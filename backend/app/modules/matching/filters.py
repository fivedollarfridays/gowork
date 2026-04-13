"""Matching engine filters — eligibility checks before scoring."""

import re

from app.cities.config import get_city_config
from app.modules.matching.types import Resource, JobMatch
from app.modules.matching.zip_validation import get_zip_regex_for_city

# Keywords indicating finance/government jobs (for medium credit severity)
FINANCE_GOV_KEYWORDS = {
    "bank", "finance", "financial", "government", "federal", "state",
    "county", "municipal", "treasury", "accounting", "auditor",
}

# Keywords indicating Sunday/night work
SUNDAY_KEYWORDS = {"sunday", "weekend", "7 days"}
NIGHT_KEYWORDS = {"night", "overnight", "10pm", "11pm", "graveyard", "third shift"}

# Certification knowledge base
CERT_DB = {
    "CNA": {
        "renewal_body": {
            "name": "Alabama Board of Nursing",
            "phone": "334-242-4060",
        },
        "training_program": {
            "name": "MRWTC",
            "program": "Healthcare Re-Certification",
        },
        "estimated_days": 45,
        "steps": [
            "Call Alabama Board of Nursing (334-242-4060) to verify license status",
            "Complete reinstatement application and pay fees",
            "Enroll in MRWTC Healthcare Re-Certification program",
            "Complete required clinical hours",
            "Submit documentation to Board for reinstatement",
        ],
    },
    "CDL": {
        "renewal_body": {
            "name": "Alabama Law Enforcement Agency",
            "phone": "334-242-4400",
        },
        "training_program": {
            "name": "Trenholm State Community College",
            "program": "CDL Training Program",
        },
        "estimated_days": 30,
        "steps": [
            "Visit Alabama Law Enforcement Agency for license status check",
            "Complete DOT physical examination",
            "Enroll in Trenholm State CDL Training Program if needed",
            "Pass CDL knowledge and skills tests",
            "Submit renewal application",
        ],
    },
    "LPN": {
        "renewal_body": {
            "name": "Alabama Board of Nursing",
            "phone": "334-242-4060",
        },
        "training_program": {
            "name": "MRWTC",
            "program": "Practical Nursing Program",
        },
        "estimated_days": 60,
        "steps": [
            "Contact Alabama Board of Nursing for reinstatement requirements",
            "Complete continuing education hours",
            "Enroll in MRWTC refresher if license lapsed > 2 years",
            "Submit reinstatement application with fees",
        ],
    },
}


def apply_credit_filter(
    jobs: list[JobMatch], credit_severity: str,
) -> tuple[list[JobMatch], list[JobMatch]]:
    """Split jobs into eligible_now vs eligible_after_repair."""
    if credit_severity == "low":
        return jobs, []

    eligible_now = []
    after_repair = []

    for job in jobs:
        if credit_severity == "high":
            if job.credit_check_required == "not_required":
                eligible_now.append(job)
            else:
                after_repair.append(job)
        else:  # medium
            title_lower = job.title.lower()
            company_lower = (job.company or "").lower()
            searchable = f"{title_lower} {company_lower}"
            if (
                job.credit_check_required == "required"
                and any(kw in searchable for kw in FINANCE_GOV_KEYWORDS)
            ):
                after_repair.append(job)
            else:
                eligible_now.append(job)

    return eligible_now, after_repair


def _check_schedule_keywords(text: str) -> str | None:
    """Check if text indicates Sunday or night work."""
    text_lower = text.lower()
    if any(kw in text_lower for kw in SUNDAY_KEYWORDS):
        return "requires personal transportation"
    if any(kw in text_lower for kw in NIGHT_KEYWORDS):
        return "requires personal transportation"
    return None


def apply_transit_filter(
    jobs: list[JobMatch], routes: list, user_zip: str,
) -> list[JobMatch]:
    """Filter jobs by M Transit accessibility."""
    has_routes = len(routes) > 0
    results = []

    for job in jobs:
        updated = job.model_copy()
        location_text = " ".join(
            filter(None, [job.title, job.location, job.company])
        )
        schedule_flag = _check_schedule_keywords(location_text)

        if schedule_flag:
            updated.eligible_after = schedule_flag
            updated.transit_accessible = False
        elif has_routes:
            updated.transit_accessible = True
            updated.route = routes[0].get("route_name", "Local Transit")

        results.append(updated)

    return results


def apply_childcare_filter(
    resources: list[Resource], user_zip: str, employer_zips: list[str],
) -> list[Resource]:
    """Filter childcare providers by proximity to home and work.

    Uses city-aware ZIP pattern from zip_validation instead of
    hardcoded Montgomery 361xx range.
    """
    relevant_zips = {user_zip} | set(employer_zips)
    city_zip_pattern = re.compile(get_zip_regex_for_city(get_city_config()))
    filtered = []

    for resource in resources:
        address = resource.address or ""
        # Check if any relevant zip appears in the address
        if any(z in address for z in relevant_zips):
            filtered.append(resource)
            continue
        # Include resources in the active city's ZIP range
        zip_match = re.search(r"\b(\d{5})\b", address)
        if zip_match and city_zip_pattern.match(zip_match.group(1)):
            filtered.append(resource)

    return filtered


def get_certification_renewal(
    work_history: str, certifications: list[dict] | None = None,
) -> list[dict]:
    """Identify certifications in work history and return renewal pathways.

    Uses city-aware cert database from resource_router.
    """
    from app.modules.matching.resource_router import get_cert_db

    city_cert_db = get_cert_db()
    results = []
    text_upper = work_history.upper()

    for cert_type, info in city_cert_db.items():
        if cert_type in text_upper:
            results.append({
                "certification_type": cert_type,
                "status": "expired",
                "renewal_body": info["renewal_body"],
                "training_program": info["training_program"],
                "estimated_days": info["estimated_days"],
                "steps": info["steps"],
            })

    return results
