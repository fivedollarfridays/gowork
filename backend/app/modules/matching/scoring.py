"""Resource relevance scoring."""

import math
import re

from app.modules.feedback.types import ResourceHealth
from app.modules.matching.types import BarrierType, Resource, UserProfile

# Weights for scoring factors (must sum to 1.0)
BARRIER_WEIGHT = 0.40
PROXIMITY_WEIGHT = 0.20
TRANSIT_WEIGHT = 0.15
SCHEDULE_WEIGHT = 0.15
INDUSTRY_WEIGHT = 0.10

# Map BarrierType to resource categories
BARRIER_CATEGORY_MAP: dict[BarrierType, set[str]] = {
    BarrierType.CREDIT: {"career_center", "social_service"},
    BarrierType.TRANSPORTATION: {"career_center", "social_service"},
    BarrierType.CHILDCARE: {"childcare", "social_service"},
    BarrierType.HOUSING: {"social_service", "career_center"},
    BarrierType.HEALTH: {"social_service", "career_center"},
    BarrierType.TRAINING: {"training", "career_center"},
    BarrierType.CRIMINAL_RECORD: {"career_center", "social_service"},
}

# Fallback for ZIPs not in the centroid table
DOWNTOWN_MONTGOMERY = (32.3668, -86.3000)

# Montgomery, AL zip code centroids (approximate lat/lng)
ZIP_CENTROIDS: dict[str, tuple[float, float]] = {
    "36101": (32.3668, -86.3000),
    "36104": (32.3750, -86.2960),
    "36105": (32.3400, -86.3100),
    "36106": (32.3800, -86.2600),
    "36107": (32.3850, -86.2800),
    "36108": (32.3600, -86.3500),
    "36109": (32.4000, -86.2500),
    "36110": (32.3200, -86.2500),
    "36111": (32.3500, -86.3200),
    "36112": (32.3800, -86.3600),
    "36113": (32.3300, -86.3400),
    "36116": (32.3100, -86.2700),
    "36117": (32.3700, -86.1800),
}

# M-Transit schedule hours (approximate)
TRANSIT_START_HOUR = 5   # 5am
TRANSIT_END_HOUR = 21    # 9pm


def haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in miles between two lat/lng points."""
    r = 3959  # Earth radius in miles
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _score_barrier_alignment(resource: Resource, profile: UserProfile) -> float:
    """Score 0-1 based on how well resource category matches user barriers."""
    for barrier in profile.primary_barriers:
        matching_categories = BARRIER_CATEGORY_MAP.get(barrier, set())
        if resource.category in matching_categories:
            return 1.0
    return 0.1  # small base score for any resource


def _score_proximity(resource: Resource, profile: UserProfile) -> float:
    """Score 0-1 based on distance. Closer = higher score."""
    if resource.lat is None or resource.lng is None:
        return 0.5  # neutral when resource location unknown
    user_coords = ZIP_CENTROIDS.get(profile.zip_code, DOWNTOWN_MONTGOMERY)
    miles = haversine_miles(user_coords[0], user_coords[1], resource.lat, resource.lng)
    if miles <= 1.0:
        return 1.0
    if miles >= 15.0:
        return 0.1
    return 1.0 - (miles - 1.0) / 14.0 * 0.9


def _score_transit(
    resource: Resource, profile: UserProfile,
    nearest_stop_miles: float | None = None,
) -> float:
    """Score 0-1 for transit accessibility.

    When ``nearest_stop_miles`` is provided, uses distance-based scoring for
    transit-dependent users.  Schedule penalties are applied as a multiplier.
    """
    if not profile.transit_dependent:
        return 0.8  # has vehicle, transit is less relevant

    # Schedule penalty multiplier
    if profile.schedule_type == "night":
        schedule_mult = 0.3
    elif profile.schedule_type == "flexible":
        schedule_mult = 0.7
    else:
        schedule_mult = 1.0

    if nearest_stop_miles is not None:
        # Distance-based scoring
        if nearest_stop_miles <= 0.25:
            dist_score = 0.9
        elif nearest_stop_miles <= 1.0:
            dist_score = 0.7
        elif nearest_stop_miles <= 3.0:
            dist_score = 0.4
        else:
            dist_score = 0.1
        return dist_score * schedule_mult

    # Fallback: schedule-only scoring (no stop data)
    return 0.9 * schedule_mult


def _score_schedule(resource: Resource, profile: UserProfile) -> float:
    """Score 0-1 for schedule compatibility."""
    if not resource.notes:
        return 0.5  # unknown hours, neutral

    notes_lower = resource.notes.lower()
    if profile.schedule_type == "daytime" and "evening" not in notes_lower:
        return 0.8
    if profile.schedule_type == "evening" and "evening" in notes_lower:
        return 0.9
    if profile.schedule_type == "night":
        return 0.3  # most resources don't offer night services
    return 0.5


def _score_industry(resource: Resource, profile: UserProfile) -> float:
    """Score 0-1 for industry alignment."""
    if not profile.target_industries:
        return 0.5  # no preference, neutral

    # Check if resource services/notes mention target industries
    searchable = " ".join(filter(None, [
        resource.subcategory,
        resource.notes,
        " ".join(resource.services or []),
    ])).lower()

    for industry in profile.target_industries:
        pattern = r"\b" + re.escape(industry.lower()) + r"\b"
        if re.search(pattern, searchable):
            return 1.0
    return 0.3


def score_resource(
    resource: Resource, profile: UserProfile,
    nearest_stop_miles: float | None = None,
) -> float:
    """Score a resource's relevance to a specific user profile.

    Returns: 0.0 - 1.0 (clamped)
    """
    score = (
        BARRIER_WEIGHT * _score_barrier_alignment(resource, profile)
        + PROXIMITY_WEIGHT * _score_proximity(resource, profile)
        + TRANSIT_WEIGHT * _score_transit(resource, profile, nearest_stop_miles)
        + SCHEDULE_WEIGHT * _score_schedule(resource, profile)
        + INDUSTRY_WEIGHT * _score_industry(resource, profile)
    )
    return max(0.0, min(1.0, score))


def get_score_band(score: float) -> str:
    """Classify a score into a band."""
    if score >= 0.80:
        return "strong_match"
    if score >= 0.60:
        return "good_match"
    if score >= 0.40:
        return "possible_match"
    return "weak_match"


def rank_resources(
    resources: list[Resource], profile: UserProfile,
    stop_distances: dict[int, float] | None = None,
) -> list[Resource]:
    """Rank resources by relevance score descending. FLAGGED resources sort last."""
    scored = [
        (score_resource(r, profile, (stop_distances or {}).get(r.id)), r)
        for r in resources
    ]
    scored.sort(
        key=lambda x: (0 if x[1].health_status == ResourceHealth.FLAGGED else 1, x[0]),
        reverse=True,
    )
    return [r for _, r in scored]
