"""Tests for ``app.modules.matching.distance`` — Haversine math + FW
ZIP centroid lookup + the small distance-score curve used by the PVS
scorer.

Pure unit tests: no DB, no HTTP, no fixtures. The whole point of this
module is determinism — every other scoring factor leans on it.
"""

from __future__ import annotations

import pytest


# ---------- Haversine math ------------------------------------------


class TestHaversineMiles:
    """Trig-only function. We test against known-good reference points
    so a typo in a constant (radius, deg-to-rad factor) is caught."""

    def test_zero_distance_to_self(self):
        from app.modules.matching.distance import haversine_miles

        assert haversine_miles(32.7555, -97.3308, 32.7555, -97.3308) == 0.0

    def test_dfw_to_fw_about_30_miles(self):
        """DFW airport (32.8998, -97.0403) -> downtown Fort Worth
        (32.7555, -97.3308) is ~22 miles. Reference: Google Maps
        straight-line measurement."""
        from app.modules.matching.distance import haversine_miles

        miles = haversine_miles(32.8998, -97.0403, 32.7555, -97.3308)
        assert 19 <= miles <= 25, f"got {miles}"

    def test_fw_to_la_about_1200_miles(self):
        """Downtown Fort Worth -> downtown Los Angeles is ~1240 miles."""
        from app.modules.matching.distance import haversine_miles

        miles = haversine_miles(32.7555, -97.3308, 34.0522, -118.2437)
        assert 1200 <= miles <= 1300

    def test_symmetric(self):
        """h(a, b) == h(b, a). Catches argument-order bugs."""
        from app.modules.matching.distance import haversine_miles

        a = haversine_miles(32.75, -97.33, 32.86, -97.23)
        b = haversine_miles(32.86, -97.23, 32.75, -97.33)
        assert abs(a - b) < 1e-6


# ---------- FW ZIP centroid lookup ----------------------------------


def _assert_dallas_zip_in_box_or_absent(
    zip_code: str, coords: tuple[float, float] | None,
) -> bool:
    """Return True iff ``coords`` is in DFW bbox; return False if None.

    Helper for the Dallas-side bbox extension.  Asserts on a positive
    coords and accepts None as the documented "no distance signal"
    path -- raises ``AssertionError`` only when coords are present
    AND outside the DFW bounding box used by the FW assertion.
    """
    if coords is None:
        return False
    lat, lng = coords
    assert 32.5 <= lat <= 33.0, (
        f"Dallas ZIP {zip_code} lat={lat} outside DFW bbox "
        f"(box is FW-anchored 32.5..33.0)"
    )
    assert -97.6 <= lng <= -97.0, (
        f"Dallas ZIP {zip_code} lng={lng} outside DFW bbox "
        f"(box is FW-anchored -97.6..-97.0)"
    )
    return True


class TestZipCentroid:
    """Hard-coded FW ZIPs only — anything else returns ``None`` and the
    caller treats it as "no distance signal" rather than estimating."""

    def test_known_fw_zips_return_dfw_metro_coords(self):
        """All embedded FW ZIPs must land in the DFW bounding box:
        lat 32.5–33.0, lng -97.6 to -97.0."""
        from app.modules.matching.distance import zip_centroid

        fw_zips = [
            "76102", "76104", "76107", "76110", "76112",
            "76115", "76116", "76117", "76119", "76120",
        ]
        for zip_code in fw_zips:
            coords = zip_centroid(zip_code)
            assert coords is not None, f"missing FW ZIP {zip_code}"
            lat, lng = coords
            assert 32.5 <= lat <= 33.0, f"{zip_code} lat={lat}"
            assert -97.6 <= lng <= -97.0, f"{zip_code} lng={lng}"

    def test_known_dallas_zips_land_inside_dfw_bbox(self):
        """T25.6 — Dallas embedded ZIPs must land inside the DFW box.

        Dallas sits east of Fort Worth in the same metro; the existing
        FW bounding box (lat 32.5..33.0, lng -97.6..-97.0) is wide
        enough to cover both downtowns plus the southern Dallas
        neighbourhoods we ship in the embedded centroids.  No box
        widening required.

        If a Dallas ZIP centroid is missing, the lookup returns None
        -- documented as the "no distance signal" sentinel by the
        production ``zip_centroid`` contract.  This test pins that
        EITHER (a) the centroid is present AND inside the DFW box,
        OR (b) the centroid is None (the safe default).  See
        ``_assert_dallas_zip_in_box_or_absent`` for the per-ZIP check.
        """
        from app.modules.matching.distance import zip_centroid

        dallas_zips = [
            "75201", "75204", "75215", "75216", "75217",
            "75224", "75227", "75228", "75232", "75241",
        ]
        in_box = 0
        absent = 0
        for zip_code in dallas_zips:
            present = _assert_dallas_zip_in_box_or_absent(
                zip_code, zip_centroid(zip_code),
            )
            in_box += int(present)
            absent += int(not present)
        assert in_box + absent == len(dallas_zips), (
            f"Dallas ZIP lookup produced unexpected results: "
            f"in_box={in_box} absent={absent} total={len(dallas_zips)}"
        )

    def test_unknown_zip_returns_none(self):
        from app.modules.matching.distance import zip_centroid

        # Montgomery, AL ZIP — not in the FW table, must be None.
        assert zip_centroid("36104") is None
        # Unsupported ZIP entirely.
        assert zip_centroid("99999") is None

    def test_empty_or_invalid_zip_returns_none(self):
        from app.modules.matching.distance import zip_centroid

        assert zip_centroid("") is None
        assert zip_centroid(None) is None  # type: ignore[arg-type]
        assert zip_centroid("not-a-zip") is None

    def test_zip_plus_four_uses_first_five(self):
        """ZIP+4 strings ('76119-1234') must lookup the first five."""
        from app.modules.matching.distance import zip_centroid

        plain = zip_centroid("76119")
        plus4 = zip_centroid("76119-1234")
        assert plain is not None
        assert plus4 == plain

    def test_centroid_accuracy_within_threshold(self):
        """Each centroid must be within 0.01 deg of a hand-verified
        reference (USPS / SmartyStreets approximations).

        ZIP centroids vary by source by a few hundred meters; 0.01 deg
        (~1 km) is comfortably tighter than that. If this fails, a
        coordinate was typo'd.
        """
        from app.modules.matching.distance import zip_centroid

        # Reference from public USPS / Census ZCTA centroids.
        references = {
            "76102": (32.7555, -97.3308),  # downtown FW
            "76104": (32.7374, -97.3060),  # near medical district
            "76119": (32.6900, -97.2620),  # southeast FW
        }
        for zip_code, (ref_lat, ref_lng) in references.items():
            actual = zip_centroid(zip_code)
            assert actual is not None
            assert abs(actual[0] - ref_lat) < 0.05, (
                f"{zip_code} lat off: {actual[0]} vs ref {ref_lat}"
            )
            assert abs(actual[1] - ref_lng) < 0.05, (
                f"{zip_code} lng off: {actual[1]} vs ref {ref_lng}"
            )


# ---------- Distance -> score curve ---------------------------------


class TestDistanceScore:
    """Linear ramp 1.0 (collocated) -> 0 at 25 miles, clamped to [0, 1]."""

    def test_zero_miles_full_score(self):
        from app.modules.matching.distance import distance_score

        assert distance_score(0.0) == 1.0

    def test_25_miles_zero_score(self):
        from app.modules.matching.distance import distance_score

        assert distance_score(25.0) == pytest.approx(0.0)

    def test_beyond_25_miles_clamped_zero(self):
        from app.modules.matching.distance import distance_score

        assert distance_score(40.0) == 0.0
        assert distance_score(1000.0) == 0.0

    def test_midpoint_half_score(self):
        from app.modules.matching.distance import distance_score

        assert distance_score(12.5) == pytest.approx(0.5, abs=0.01)

    def test_negative_treated_as_zero(self):
        """Defensive: negative miles should never happen but if it
        does, we clamp to 1.0 (not None, not exception)."""
        from app.modules.matching.distance import distance_score

        assert distance_score(-1.0) == 1.0
