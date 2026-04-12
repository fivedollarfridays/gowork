"""Criminal record clearing router -- selects AL or TX rules by city config."""

from __future__ import annotations

from app.cities.config import get_city_config
from app.modules.criminal.record_profile import RecordProfile


def check_record_clearing(
    profile: RecordProfile | None,
):
    """Route record clearing check to the correct state module.

    Returns:
        Alabama: ExpungementResult
        Texas: TexasRecordClearingResult
    """
    state = get_city_config().state
    if state == "TX":
        from app.modules.criminal.texas_expunction import check_texas_record_clearing
        return check_texas_record_clearing(profile)
    # Default: Alabama
    from app.modules.criminal.expungement import check_expungement_eligibility
    return check_expungement_eligibility(profile)
