"""Resource affinity routing -- specialized resources claim their barrier card.

City-aware: uses resource_router for affinity keywords at call time.
Module-level constants are Montgomery defaults (used by resource_router
for Montgomery routing).
"""

from app.modules.matching.resource_router import get_resource_affinity
from app.modules.matching.scoring import BARRIER_CATEGORY_MAP
from app.modules.matching.types import BarrierType, Resource

# Process the most-specialized barriers first so their category-fallback
# routing (Phase 2 in assign_resources) claims social_service resources
# before the broader barriers can sweep them.
#
# CHILDCARE and TRAINING come BEFORE TRANSPORTATION because all three map
# to {social_service, ...} in BARRIER_CATEGORY_MAP — if TRANSPORTATION
# processes first it claims every social_service resource and the
# childcare/training cards end up with only their explicit category
# matches. Putting the narrower categories first keeps the specialized
# cards rich.
BARRIER_PROCESSING_ORDER: list[BarrierType] = [
    BarrierType.CHILDCARE,
    BarrierType.TRAINING,
    BarrierType.TRANSPORTATION,
    BarrierType.HEALTH,
    BarrierType.HOUSING,
    BarrierType.CREDIT,
    BarrierType.CRIMINAL_RECORD,
]

# Montgomery resource name keywords (legacy -- resource_router imports this)
RESOURCE_AFFINITY: dict[str, BarrierType] = {
    "mats": BarrierType.TRANSPORTATION,
    "montgomery area transit": BarrierType.TRANSPORTATION,
    "dhr": BarrierType.CHILDCARE,
    "department of human resources": BarrierType.CHILDCARE,
    "childcare": BarrierType.CHILDCARE,
    "credit": BarrierType.CREDIT,
    "mrwtc": BarrierType.TRAINING,
    "montgomery regional workforce": BarrierType.TRAINING,
    "workforce training": BarrierType.TRAINING,
    "legal aid": BarrierType.CRIMINAL_RECORD,
    "re-entry": BarrierType.CRIMINAL_RECORD,
    "reentry": BarrierType.CRIMINAL_RECORD,
    "expungement": BarrierType.CRIMINAL_RECORD,
}

# Montgomery career center step (legacy -- resource_router imports this)
CAREER_CENTER_STEP = (
    "Montgomery Career Center, 334-286-1746, "
    "1060 East South Boulevard, Montgomery, AL 36116"
)


def is_career_center(resource: Resource) -> bool:
    """Check if a resource is a general-purpose career center."""
    return "career center" in resource.name.lower()


def get_affinity_barrier(resource: Resource) -> BarrierType | None:
    """Return the designated barrier type for an affinity resource, or None.

    Stage-2 resolution order:
    1. Explicit ``barrier_affinity`` field on the Resource (first tag
       wins, falls back to subsequent tags only via :func:`get_affinity_barriers`).
    2. City-aware name-keyword heuristic (legacy path).
    """
    explicit = get_affinity_barriers(resource)
    if explicit:
        return explicit[0]
    affinity = get_resource_affinity()
    name_lower = resource.name.lower()
    for keyword, barrier in affinity.items():
        if keyword in name_lower:
            return barrier
    return None


def get_affinity_barriers(resource: Resource) -> list[BarrierType]:
    """Return ALL explicit barrier_affinity tags as BarrierType values.

    Stage-2: a single resource (e.g. Catholic Charities) can serve
    multiple barriers (transportation + criminal_record + housing), so
    contextual TWC slicing returns every match instead of the first.
    """
    raw = list(getattr(resource, "barrier_affinity", []) or [])
    out: list[BarrierType] = []
    for tag in raw:
        try:
            out.append(BarrierType(tag))
        except ValueError:
            continue  # tolerate unknown / typo'd tags
    return out


def _resource_barriers(resource: Resource) -> set[BarrierType]:
    """Return every barrier this resource can claim via explicit affinity."""
    explicit = set(get_affinity_barriers(resource))
    if explicit:
        return explicit
    legacy = get_affinity_barrier(resource)
    return {legacy} if legacy is not None else set()


def assign_resources(
    user_barriers: set[BarrierType], resources: list[Resource],
) -> dict[BarrierType, list[Resource]]:
    """Assign resources to barrier cards using affinity routing.

    Phase 1: Resources with explicit ``barrier_affinity`` tags claim
    every matching card the user has (a Catholic Charities entry tagged
    [transportation, criminal_record] surfaces on both cards if the
    user has both barriers).
    Phase 2: Legacy single-barrier name-keyword affinity (claim once).
    Phase 3: Remaining resources assigned by category match.
    Career centers are excluded from all cards.
    """
    claimed_ids: set[int] = set()
    card_resources: dict[BarrierType, list[Resource]] = {b: [] for b in user_barriers}

    # Phase 1 — explicit barrier_affinity tags can multi-claim
    for barrier in BARRIER_PROCESSING_ORDER:
        if barrier not in user_barriers:
            continue
        for r in resources:
            if is_career_center(r):
                continue
            tags = set(get_affinity_barriers(r))
            if barrier in tags:
                if r not in card_resources[barrier]:
                    card_resources[barrier].append(r)
                claimed_ids.add(r.id)

    # Phase 2 — legacy keyword-based single-barrier claim
    for barrier in BARRIER_PROCESSING_ORDER:
        if barrier not in user_barriers:
            continue
        for r in resources:
            if r.id in claimed_ids or is_career_center(r):
                continue
            if get_affinity_barrier(r) == barrier:
                card_resources[barrier].append(r)
                claimed_ids.add(r.id)

    # Phase 3 — category fallback
    # Resources with EXPLICIT barrier_affinity tags only land on the
    # barriers they declared.  Untagged resources still fall through to
    # the category map so the legacy data stays routable.
    for barrier in BARRIER_PROCESSING_ORDER:
        if barrier not in user_barriers:
            continue
        matching_categories = BARRIER_CATEGORY_MAP.get(barrier, set())
        for r in resources:
            if r.id in claimed_ids or is_career_center(r):
                continue
            if get_affinity_barriers(r):
                continue  # explicit-tag resources stay surgical
            if r.category in matching_categories:
                card_resources[barrier].append(r)
                claimed_ids.add(r.id)

    return card_resources
