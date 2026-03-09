"""findhelp.org capability URL generation for barrier-based program discovery."""

from app.modules.matching.types import BarrierType

# Maps each barrier type to a findhelp.org category path.
# URL pattern: https://www.findhelp.org/{path}--montgomery-al?postal={zip}
# SYNC: frontend/src/lib/findhelp.ts — keep mappings in lockstep
FINDHELP_CATEGORIES: dict[BarrierType, str] = {
    BarrierType.CREDIT: "money/financial-assistance",
    BarrierType.TRANSPORTATION: "transit/transportation",
    BarrierType.CHILDCARE: "care/childcare",
    BarrierType.HOUSING: "housing/housing",
    BarrierType.HEALTH: "health/health-care",
    BarrierType.TRAINING: "work/job-training",
    BarrierType.CRIMINAL_RECORD: "work/help-for-the-formerly-incarcerated",
}

_BASE = "https://www.findhelp.org"


def generate_findhelp_url(barrier_type: BarrierType | str, zip_code: str) -> str | None:
    """Generate a findhelp.org capability URL for a barrier + zip code.

    Returns None if the barrier type has no mapping.
    """
    path = FINDHELP_CATEGORIES.get(barrier_type)
    if path is None:
        return None
    return f"{_BASE}/{path}--montgomery-al?postal={zip_code}"
