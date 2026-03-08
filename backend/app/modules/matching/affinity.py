"""Resource affinity routing — specialized resources claim their barrier card."""

from app.modules.matching.career_center_package import CAREER_CENTER
from app.modules.matching.scoring import BARRIER_CATEGORY_MAP
from app.modules.matching.types import BarrierType, Resource

# Process specialized barriers first so their affinity resources get claimed
BARRIER_PROCESSING_ORDER: list[BarrierType] = [
    BarrierType.TRANSPORTATION,
    BarrierType.CHILDCARE,
    BarrierType.TRAINING,
    BarrierType.HEALTH,
    BarrierType.HOUSING,
    BarrierType.CREDIT,
    BarrierType.CRIMINAL_RECORD,
]

# Resource name keywords → designated barrier type
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
}

CAREER_CENTER_STEP = (
    f"Start here: {CAREER_CENTER.name} — {CAREER_CENTER.phone}, {CAREER_CENTER.address}"
)


def is_career_center(resource: Resource) -> bool:
    """Check if a resource is a general-purpose career center."""
    return "career center" in resource.name.lower()


def get_affinity_barrier(resource: Resource) -> BarrierType | None:
    """Return the designated barrier type for an affinity resource, or None."""
    name_lower = resource.name.lower()
    for keyword, barrier in RESOURCE_AFFINITY.items():
        if keyword in name_lower:
            return barrier
    return None


def assign_resources(
    user_barriers: set[BarrierType], resources: list[Resource],
) -> dict[BarrierType, list[Resource]]:
    """Assign resources to barrier cards using affinity routing.

    Phase 1: Affinity resources claimed by their designated barrier.
    Phase 2: Remaining resources assigned by category match.
    Career centers are excluded from all cards.
    """
    claimed_ids: set[int] = set()
    card_resources: dict[BarrierType, list[Resource]] = {b: [] for b in user_barriers}

    for barrier in BARRIER_PROCESSING_ORDER:
        if barrier not in user_barriers:
            continue
        for r in resources:
            if r.id in claimed_ids or is_career_center(r):
                continue
            if get_affinity_barrier(r) == barrier:
                card_resources[barrier].append(r)
                claimed_ids.add(r.id)

    for barrier in BARRIER_PROCESSING_ORDER:
        if barrier not in user_barriers:
            continue
        matching_categories = BARRIER_CATEGORY_MAP.get(barrier, set())
        for r in resources:
            if r.id in claimed_ids or is_career_center(r):
                continue
            if r.category in matching_categories:
                card_resources[barrier].append(r)
                claimed_ids.add(r.id)

    return card_resources
