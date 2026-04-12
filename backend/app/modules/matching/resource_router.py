"""Resource router -- selects city-specific resources by city config."""

from app.cities.config import get_city_config
from app.modules.matching.career_center_types import CareerCenterInfo
from app.modules.matching.types import BarrierType


def get_career_center() -> CareerCenterInfo:
    """Return career center info for the active city."""
    state = get_city_config().state
    if state == "TX":
        from app.modules.matching.fort_worth_resources import CAREER_CENTER
        return CAREER_CENTER
    from app.modules.matching.career_center_package import CAREER_CENTER
    return CAREER_CENTER


def get_barrier_actions() -> dict[BarrierType, list[str]]:
    """Return barrier action steps for the active city."""
    state = get_city_config().state
    if state == "TX":
        from app.modules.matching.fort_worth_resources import BARRIER_ACTIONS
        return BARRIER_ACTIONS
    from app.modules.matching.barrier_cards import BARRIER_ACTIONS
    return BARRIER_ACTIONS


def get_career_center_step() -> str:
    """Return the career center step string for the active city."""
    state = get_city_config().state
    if state == "TX":
        from app.modules.matching.fort_worth_resources import CAREER_CENTER_STEP
        return CAREER_CENTER_STEP
    from app.modules.matching.affinity import CAREER_CENTER_STEP
    return CAREER_CENTER_STEP


def get_resource_affinity() -> dict[str, BarrierType]:
    """Return resource affinity keywords for the active city."""
    state = get_city_config().state
    if state == "TX":
        from app.modules.matching.fort_worth_resources import RESOURCE_AFFINITY
        return RESOURCE_AFFINITY
    from app.modules.matching.affinity import RESOURCE_AFFINITY
    return RESOURCE_AFFINITY


def get_cert_db() -> dict:
    """Return certification database for the active city."""
    state = get_city_config().state
    if state == "TX":
        from app.modules.matching.fort_worth_resources import CERT_DB
        return CERT_DB
    from app.modules.matching.filters import CERT_DB
    return CERT_DB
