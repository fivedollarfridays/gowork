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
    return frozenset({
        "SNAP", "TANF", "Medicaid", "ALL_Kids",
        "Childcare_Subsidy", "Section_8", "LIHEAP",
    })


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


def get_thresholds() -> dict:
    """Return the thresholds module for the active city's state.

    Returns a dict with keys matching the threshold constants:
    FPL_2026, TANF_MAX_MONTHLY, SMI_2026, CHILDCARE_SMI_LIMIT_PCT,
    SECTION_8_AMI_LIMIT_PCT, AMI (city-specific), etc.
    """
    state = get_city_config().state
    if state == "TX":
        from app.modules.benefits.texas import thresholds as tx
        return {
            "FPL_2026": tx.FPL_2026,
            "TANF_MAX_MONTHLY": tx.TANF_MAX_MONTHLY,
            "SMI_2026": tx.SMI_2026,
            "CHILDCARE_SMI_LIMIT_PCT": tx.CHILDCARE_SMI_LIMIT_PCT,
            "AMI": tx.AMI_FORT_WORTH_2026,
            "SECTION_8_AMI_LIMIT_PCT": tx.SECTION_8_AMI_LIMIT_PCT,
            "FICA_RATE": tx.FICA_RATE,
            "TAX_BRACKETS": tx.TAX_BRACKETS,
            "CHILD_HEALTH_FPL_PCT": tx.CHIP_FPL_PCT,
            "CHILD_HEALTH_PROGRAM": "CHIP",
            "ENERGY_FPL_LIMIT_PCT": tx.CEAP_FPL_LIMIT_PCT,
            "ENERGY_PROGRAM": "CEAP",
        }
    from app.modules.benefits import thresholds as al
    return {
        "FPL_2026": al.FPL_2026,
        "TANF_MAX_MONTHLY": al.TANF_MAX_MONTHLY,
        "SMI_2026": al.SMI_2026,
        "CHILDCARE_SMI_LIMIT_PCT": al.CHILDCARE_SMI_LIMIT_PCT,
        "AMI": al.AMI_MONTGOMERY_2026,
        "SECTION_8_AMI_LIMIT_PCT": al.SECTION_8_AMI_LIMIT_PCT,
        "FICA_RATE": al.FICA_RATE,
        "TAX_BRACKETS": al.TAX_BRACKETS,
        "CHILD_HEALTH_FPL_PCT": al.ALL_KIDS_FPL_PCT,
        "CHILD_HEALTH_PROGRAM": "ALL_Kids",
        "ENERGY_FPL_LIMIT_PCT": al.LIHEAP_FPL_LIMIT_PCT,
        "ENERGY_PROGRAM": "LIHEAP",
    }


def get_sum_program_benefits():
    """Return the sum_program_benefits function for the active city's state."""
    state = get_city_config().state
    if state == "TX":
        from app.modules.benefits.texas.program_calculators import sum_program_benefits
        return sum_program_benefits
    from app.modules.benefits.program_calculators import sum_program_benefits
    return sum_program_benefits
