"""Proximity scoring for job matches using haversine distance."""

import re

from app.modules.matching.geo_router import get_downtown_coords, get_zip_centroids
from app.modules.matching.scoring import distance_to_score, haversine_miles

_ZIP_RE = re.compile(r"\b(\d{5})\b")

# Re-export for existing test imports
_distance_to_score = distance_to_score


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

    centroids = get_zip_centroids()
    downtown = get_downtown_coords()
    user_coords = centroids.get(user_zip, downtown)
    job_coords = centroids.get(job_zip, downtown) if job_zip else downtown

    miles = haversine_miles(
        user_coords[0], user_coords[1], job_coords[0], job_coords[1]
    )

    score = distance_to_score(miles)

    if transit_dependent:
        score = score ** 1.5

    return score
