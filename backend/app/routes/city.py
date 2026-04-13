"""City configuration API endpoint."""

from fastapi import APIRouter

from app.cities.config import get_city_config

router = APIRouter(prefix="/api", tags=["city"])


@router.get("/city")
async def get_city() -> dict:
    """Return the active city configuration for frontend use."""
    config = get_city_config()
    return {
        "name": config.name,
        "state": config.state,
        "location": config.location,
        "zip_ranges": config.zip_ranges,
    }
