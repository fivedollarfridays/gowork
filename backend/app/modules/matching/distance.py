"""Distance utilities for the matcher.

Pure-Python Haversine + a small static lookup of FW ZIP centroids.
Used by the PVS scorer to add a distance-from-home boost when the
user lacks a vehicle.

No HTTP, no DB, no LLM in this module — every output is a deterministic
function of its inputs. That keeps the persona regression suite stable
and the scorer cheap to call millions of times during tuning sweeps.
"""

from __future__ import annotations

import math
from typing import Optional

# Earth radius in miles (mean radius — sufficient for ~25-mile commute
# scoring; the WGS-84 ellipsoid math costs more without changing rank).
_EARTH_RADIUS_MILES = 3958.8

# Distance ramp: full boost at 0 miles, zero boost at 25 miles.  Beyond
# 25 the user's reach via transit / rideshare is too constrained for
# the boost to be honest.  Tweak by changing this single constant.
_DISTANCE_FULL_SCORE_RANGE_MILES = 25.0


# ---------- Haversine ----------------------------------------------


def haversine_miles(
    lat1: float, lng1: float, lat2: float, lng2: float,
) -> float:
    """Great-circle distance between two lat/lng points, in miles.

    Pure stdlib trig; symmetric, deterministic, no rounding bias.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return _EARTH_RADIUS_MILES * c


# ---------- Fort Worth ZIP centroid lookup -------------------------

# Embedded centroids for the most common Fort Worth ZIPs.  Sources:
# public USPS / Census ZCTA centroid datasets, rounded to 4 decimal
# places (~10 m precision — plenty for commute scoring).  We only ship
# these inline because the dispatch is FW-specific; expanding to other
# cities is a separate task with its own data source.
_FW_ZIP_CENTROIDS: dict[str, tuple[float, float]] = {
    "76102": (32.7555, -97.3308),  # downtown
    "76104": (32.7374, -97.3060),  # medical district
    "76107": (32.7457, -97.3895),  # cultural / west FW
    "76110": (32.7068, -97.3389),  # south FW / TCU edge
    "76112": (32.7517, -97.2200),  # east FW
    "76115": (32.6822, -97.3486),  # south FW
    "76116": (32.7186, -97.4423),  # west / Ridglea
    "76117": (32.8113, -97.2787),  # northeast / Haltom City
    "76119": (32.6900, -97.2620),  # southeast FW
    "76120": (32.7588, -97.1880),  # east / Woodhaven
    "76123": (32.6280, -97.3920),  # southwest
    "76127": (32.7700, -97.4400),  # NAS JRB / west
    "76135": (32.8080, -97.4470),  # Lake Worth
    "76148": (32.8665, -97.2850),  # north / Watauga
    "76164": (32.7715, -97.3600),  # northside / stockyards
}


def _normalize_zip(zip_code: str) -> Optional[str]:
    """Strip ZIP+4, return the 5-digit base or None on bad input."""
    if not zip_code or not isinstance(zip_code, str):
        return None
    base = zip_code.split("-", 1)[0].strip()
    if len(base) != 5 or not base.isdigit():
        return None
    return base


def zip_centroid(zip_code: str) -> Optional[tuple[float, float]]:
    """Return (lat, lng) for known FW ZIPs, or None.

    Unknown ZIPs return None — the caller treats that as "no distance
    signal" and skips the boost.  We do not estimate centroids for
    out-of-table ZIPs because guessing would silently break personas
    in other service areas.
    """
    base = _normalize_zip(zip_code)
    if base is None:
        return None
    return _FW_ZIP_CENTROIDS.get(base)


# ---------- Distance -> score curve --------------------------------


def distance_score(miles: float) -> float:
    """Map a mileage to a 0..1 boost.

    1.0 at the home ZIP, linearly down to 0.0 at 25 miles, clamped
    everywhere outside.  Negative miles (defensive) clamp to 1.0;
    the function never raises.
    """
    if miles <= 0.0:
        return 1.0
    if miles >= _DISTANCE_FULL_SCORE_RANGE_MILES:
        return 0.0
    return 1.0 - (miles / _DISTANCE_FULL_SCORE_RANGE_MILES)


def compute_job_distance(
    user_zip: str,
    job_lat: Optional[float],
    job_lng: Optional[float],
) -> Optional[float]:
    """Resolve user ZIP -> centroid, return miles to job, or None.

    Returns None when:

    * user ZIP is missing or not in the FW lookup;
    * the job has no lat/lng (un-geocoded).

    None is the "no distance signal" sentinel the scorer uses to
    suppress the boost without inventing a number.
    """
    if job_lat is None or job_lng is None:
        return None
    centroid = zip_centroid(user_zip)
    if centroid is None:
        return None
    return haversine_miles(centroid[0], centroid[1], job_lat, job_lng)
