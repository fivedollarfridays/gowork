"""Proximity scoring for job matches using haversine distance."""

import re

from app.modules.matching.scoring import (
    DOWNTOWN_MONTGOMERY,
    ZIP_CENTROIDS,
    distance_to_score,
    haversine_miles,
)

_ZIP_RE = re.compile(r"\b(\d{5})\b")


def extract_zip(location: str) -> str | None:
    """Extract 5-digit zip from location string. Returns last match."""
    matches = _ZIP_RE.findall(location)
    if not matches:
        return None
    return matches[-1]


def score_proximity(
    user_zip: str, job_location: str, transit_dependent: bool
) -> float:
    """Score 0.0-1.0 based on haversine distance between user and job.

    Uses ZIP_CENTROIDS for known zips, falls back to DOWNTOWN_MONTGOMERY.
    Transit penalty: score ** 1.5 for transit-dependent users.
    """
    job_zip = extract_zip(job_location)

    user_coords = ZIP_CENTROIDS.get(user_zip, DOWNTOWN_MONTGOMERY)
    job_coords = ZIP_CENTROIDS.get(job_zip, DOWNTOWN_MONTGOMERY) if job_zip else DOWNTOWN_MONTGOMERY

    miles = haversine_miles(
        user_coords[0], user_coords[1], job_coords[0], job_coords[1]
    )

    score = distance_to_score(miles)

    if transit_dependent:
        score = score ** 1.5

    return score
