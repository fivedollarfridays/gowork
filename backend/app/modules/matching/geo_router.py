"""Geo data router -- selects Montgomery or Fort Worth data by city config."""

from app.cities.config import get_city_config


def get_downtown_coords() -> tuple[float, float]:
    """Return downtown coordinates for the active city."""
    state = get_city_config().state
    if state == "TX":
        from app.modules.matching.fort_worth_geo import DOWNTOWN_FORT_WORTH
        return DOWNTOWN_FORT_WORTH
    from app.modules.matching.scoring import DOWNTOWN_MONTGOMERY
    return DOWNTOWN_MONTGOMERY


def get_zip_centroids() -> dict[str, tuple[float, float]]:
    """Return ZIP centroids for the active city."""
    state = get_city_config().state
    if state == "TX":
        from app.modules.matching.fort_worth_geo import ZIP_CENTROIDS
        return ZIP_CENTROIDS
    from app.modules.matching.scoring import ZIP_CENTROIDS
    return ZIP_CENTROIDS


def get_transit_hours() -> tuple[int, int]:
    """Return (start_hour, end_hour) for the active city's transit system."""
    state = get_city_config().state
    if state == "TX":
        from app.modules.matching.fort_worth_geo import (
            TRANSIT_START_HOUR,
            TRANSIT_END_HOUR,
        )
        return TRANSIT_START_HOUR, TRANSIT_END_HOUR
    from app.modules.matching.scoring import TRANSIT_START_HOUR, TRANSIT_END_HOUR
    return TRANSIT_START_HOUR, TRANSIT_END_HOUR
