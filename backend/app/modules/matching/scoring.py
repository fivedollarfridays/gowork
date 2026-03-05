"""Resource relevance scoring."""

import math

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
    BarrierType.TRANSPORTATION: {"career_center"},
    BarrierType.CHILDCARE: {"childcare"},
    BarrierType.HOUSING: {"social_service"},
    BarrierType.HEALTH: {"social_service"},
    BarrierType.TRAINING: {"training", "career_center"},
    BarrierType.CRIMINAL_RECORD: {"career_center", "social_service"},
}

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


def _haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
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
    user_coords = ZIP_CENTROIDS.get(profile.zip_code)
    if not user_coords or not resource.address:
        return 0.5  # neutral when location unknown
    # Resources don't have lat/lng in the Resource model, so use neutral
    return 0.5


def _score_transit(resource: Resource, profile: UserProfile) -> float:
    """Score 0-1 for transit accessibility. Penalize transit-dependent users
    when resource requires Sunday/night access (M-Transit constraint)."""
    if not profile.transit_dependent:
        return 0.8  # has vehicle, transit is less relevant

    # Check schedule: if user needs night hours, penalize
    if profile.schedule_type == "night":
        return 0.2  # M-Transit ends at 9pm

    # Check if user needs Sunday access
    if profile.schedule_type == "flexible":
        return 0.6  # some risk of Sunday need

    # Daytime/evening within M-Transit hours
    return 0.9


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
        if industry.lower() in searchable:
            return 1.0
    return 0.3


def score_resource(resource: Resource, profile: UserProfile) -> float:
    """Score a resource's relevance to a specific user profile.

    Returns: 0.0 - 1.0 (clamped)
    """
    score = (
        BARRIER_WEIGHT * _score_barrier_alignment(resource, profile)
        + PROXIMITY_WEIGHT * _score_proximity(resource, profile)
        + TRANSIT_WEIGHT * _score_transit(resource, profile)
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
) -> list[Resource]:
    """Rank resources by relevance score, descending."""
    scored = [(score_resource(r, profile), r) for r in resources]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored]
