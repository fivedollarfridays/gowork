"""Benefits module router -- selects AL or TX modules based on city config.

The CITY env var (via CityConfig.state) determines which state's benefit
rules, thresholds, application data, and program names to use.
"""

from app.cities.config import get_city_config
from app.modules.benefits.types import ProgramApplicationInfo


def get_program_checks() -> dict:
    """Return the program eligibility check functions for the active city's state."""
    state = get_city_config().state
    if state == "TX":
        from app.modules.benefits.texas.eligibility_checks import PROGRAM_CHECKS
        return PROGRAM_CHECKS
    # Default: Alabama
    from app.modules.benefits.eligibility_checks import PROGRAM_CHECKS
    return PROGRAM_CHECKS


def get_application_data() -> dict[str, ProgramApplicationInfo]:
    """Return application data for the active city's state."""
    state = get_city_config().state
    if state == "TX":
        from app.modules.benefits.texas.application_data import APPLICATION_DATA
        return APPLICATION_DATA
    from app.modules.benefits.application_data import APPLICATION_DATA
    return APPLICATION_DATA


def get_program_calculators() -> dict:
    """Return program calculator functions for the active city's state."""
    state = get_city_config().state
    if state == "TX":
        from app.modules.benefits.texas.program_calculators import PROGRAM_CALCULATORS
        return PROGRAM_CALCULATORS
    from app.modules.benefits.program_calculators import PROGRAM_CALCULATORS
    return PROGRAM_CALCULATORS


def get_valid_programs() -> frozenset[str]:
    """Return the set of valid program names for the active city's state."""
    state = get_city_config().state
    if state == "TX":
        return frozenset({
            "SNAP", "TANF", "Medicaid", "CHIP",
            "Childcare_Subsidy", "Section_8", "CEAP",
        })
    from app.modules.benefits.types import VALID_PROGRAMS
    return VALID_PROGRAMS


def get_screener_disclaimer() -> str:
    """Return the benefits screener disclaimer for the active city's state."""
    state = get_city_config().state
    if state == "TX":
        return (
            "This is an estimate based on general program rules. "
            "Contact the Texas Health and Human Services Commission (HHSC) "
            "for an official eligibility determination."
        )
    return (
        "This is an estimate based on general program rules. "
        "Contact the Alabama Department of Human Resources (DHR) "
        "for an official eligibility determination."
    )


def get_application_info(program: str) -> ProgramApplicationInfo | None:
    """Look up application info for a program in the active city's state."""
    data = get_application_data()
    return data.get(program)
