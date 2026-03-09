"""Commute time estimator using haversine distance + average speed formulas.

Calculates approximate drive, transit, and walk times for Montgomery, AL
without external API calls.
"""

from app.modules.matching.proximity_scorer import extract_zip
from app.modules.matching.scoring import (
    DOWNTOWN_MONTGOMERY,
    ZIP_CENTROIDS,
    haversine_miles,
)
from app.modules.matching.types_transit import CommuteEstimate, TransitInfo

# Average speeds for Montgomery, AL
_DRIVE_MPH = 25       # city driving
_BUS_MPH = 12         # M-Transit average
_WALK_MPH = 3         # walking speed
_AVG_WAIT_MIN = 10    # average bus wait
_WALK_FROM_STOP_MIN = 5  # estimated walk from bus stop to job
_MAX_WALK_MILES = 2.0  # beyond this, walk time is None


def _resolve_coords(
    user_zip: str, job_location: str,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Resolve user and job coordinates from ZIP codes."""
    user_coords = ZIP_CENTROIDS.get(user_zip, DOWNTOWN_MONTGOMERY)
    job_zip = extract_zip(job_location)
    job_coords = (
        ZIP_CENTROIDS.get(job_zip, DOWNTOWN_MONTGOMERY) if job_zip else DOWNTOWN_MONTGOMERY
    )
    return user_coords, job_coords


def _drive_minutes(distance_miles: float) -> int:
    """Calculate drive time in minutes. Minimum 1 minute."""
    return max(1, round(distance_miles / _DRIVE_MPH * 60))


def _walk_minutes(distance_miles: float) -> int | None:
    """Calculate walk time if within walkable distance. None if too far."""
    if distance_miles > _MAX_WALK_MILES:
        return None
    return max(1, round(distance_miles / _WALK_MPH * 60))


def _transit_minutes(
    distance_miles: float, transit_info: TransitInfo | None,
) -> int | None:
    """Calculate transit time using walk + wait + ride + walk from stop.

    Returns None if no transit_info or no serving routes.
    """
    if transit_info is None or not transit_info.serving_routes:
        return None

    min_walk_miles = min(r.walk_miles for r in transit_info.serving_routes)
    walk_to_stop_min = max(1, round(min_walk_miles / _WALK_MPH * 60))
    ride_min = max(1, round(distance_miles / _BUS_MPH * 60))
    total = walk_to_stop_min + _AVG_WAIT_MIN + ride_min + _WALK_FROM_STOP_MIN
    return total


def estimate_commute(
    user_zip: str,
    job_location: str,
    transit_info: TransitInfo | None = None,
) -> CommuteEstimate:
    """Estimate commute times (drive, transit, walk) between user and job.

    Uses haversine distance with average speed formulas:
    - Drive: 25 mph city driving
    - Transit: walk to stop + 10 min wait + 12 mph bus + 5 min walk from stop
    - Walk: 3 mph, only if distance <= 2.0 miles
    """
    user_coords, job_coords = _resolve_coords(user_zip, job_location)
    distance = haversine_miles(
        user_coords[0], user_coords[1], job_coords[0], job_coords[1],
    )

    return CommuteEstimate(
        drive_min=_drive_minutes(distance),
        transit_min=_transit_minutes(distance, transit_info),
        walk_min=_walk_minutes(distance),
    )
