"""WP2 contract: TWC presents 5 surgical slices, not one always-show.

Verifies that the Stage-2 TWC slices in
``backend/data/cities/fort-worth/resources.json`` are tagged so the
correct slice surfaces per barrier mix:

- TRAINING -> 'TWC Training Programs ... (WIOA Vouchers)'
- TRANSPORTATION -> 'TWC Transportation Vouchers'
- CRIMINAL_RECORD -> 'TWC Reentry Program'
- CHILDCARE -> 'TWC Child Care Subsidy'
- (no specific barrier) -> 'TWC General Job Search' (untagged, surfaces
  via legacy career_center / general path)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.modules.matching.affinity import assign_resources
from app.modules.matching.types import BarrierType, Resource

_RESOURCES_PATH = (
    Path(__file__).parent.parent / "data" / "cities" / "fort-worth"
    / "resources.json"
)


@pytest.fixture(scope="module")
def fw_resources() -> list[Resource]:
    """Load Fort Worth resources as Resource models with stable ids."""
    with _RESOURCES_PATH.open(encoding="utf-8") as f:
        raw = json.load(f)
    return [Resource(id=i + 1, **entry) for i, entry in enumerate(raw)]


def _names_on_card(
    cards: dict[BarrierType, list[Resource]], barrier: BarrierType,
) -> list[str]:
    return [r.name for r in cards.get(barrier, [])]


class TestTWCContextualSlicing:
    def test_training_barrier_surfaces_wioa_voucher_slice(
        self, fw_resources: list[Resource],
    ) -> None:
        cards = assign_resources({BarrierType.TRAINING}, fw_resources)
        names = _names_on_card(cards, BarrierType.TRAINING)
        assert any("TWC Training Programs" in n for n in names), names

    def test_transportation_barrier_surfaces_voucher_slice(
        self, fw_resources: list[Resource],
    ) -> None:
        cards = assign_resources({BarrierType.TRANSPORTATION}, fw_resources)
        names = _names_on_card(cards, BarrierType.TRANSPORTATION)
        assert any("TWC Transportation Vouchers" in n for n in names), names

    def test_criminal_record_barrier_surfaces_reentry_slice(
        self, fw_resources: list[Resource],
    ) -> None:
        cards = assign_resources({BarrierType.CRIMINAL_RECORD}, fw_resources)
        names = _names_on_card(cards, BarrierType.CRIMINAL_RECORD)
        assert any("TWC Reentry Program" in n for n in names), names

    def test_childcare_barrier_surfaces_child_care_subsidy_slice(
        self, fw_resources: list[Resource],
    ) -> None:
        cards = assign_resources({BarrierType.CHILDCARE}, fw_resources)
        names = _names_on_card(cards, BarrierType.CHILDCARE)
        assert any("TWC Child Care Subsidy" in n for n in names), names

    def test_training_card_does_not_get_transportation_slice(
        self, fw_resources: list[Resource],
    ) -> None:
        """Each slice routes to ITS OWN barrier, not all of them."""
        cards = assign_resources({BarrierType.TRAINING}, fw_resources)
        names = _names_on_card(cards, BarrierType.TRAINING)
        assert not any("Transportation Vouchers" in n for n in names), names

    def test_transportation_card_does_not_get_reentry_slice(
        self, fw_resources: list[Resource],
    ) -> None:
        cards = assign_resources({BarrierType.TRANSPORTATION}, fw_resources)
        names = _names_on_card(cards, BarrierType.TRANSPORTATION)
        assert not any("TWC Reentry Program" in n for n in names), names


class TestTransportationFloorIsRich:
    """WP3 lockdown: ~20 transportation entries cover the major modes."""

    def test_has_at_least_15_transportation_resources(
        self, fw_resources: list[Resource],
    ) -> None:
        transport = [
            r for r in fw_resources
            if "transportation" in (r.barrier_affinity or [])
        ]
        assert len(transport) >= 15, f"Only {len(transport)} transport-tagged"

    def test_covers_public_transit_subcategory(
        self, fw_resources: list[Resource],
    ) -> None:
        subs = {r.subcategory for r in fw_resources if r.subcategory}
        assert "public_transit" in subs

    def test_covers_vehicle_repair_subcategory(
        self, fw_resources: list[Resource],
    ) -> None:
        subs = {r.subcategory for r in fw_resources if r.subcategory}
        assert "vehicle_repair" in subs

    def test_covers_medical_transport_subcategory(
        self, fw_resources: list[Resource],
    ) -> None:
        subs = {r.subcategory for r in fw_resources if r.subcategory}
        assert "medical_transport" in subs

    def test_covers_license_restoration_subcategory(
        self, fw_resources: list[Resource],
    ) -> None:
        subs = {r.subcategory for r in fw_resources if r.subcategory}
        assert "license_restoration" in subs

    def test_modivcare_present_with_phone(
        self, fw_resources: list[Resource],
    ) -> None:
        modivcare = next(
            (r for r in fw_resources if "ModivCare" in r.name), None,
        )
        assert modivcare is not None
        assert modivcare.phone == "855-687-4786"

    def test_aircheck_texas_present(
        self, fw_resources: list[Resource],
    ) -> None:
        aircheck = next(
            (r for r in fw_resources if "AirCheck Texas" in r.name), None,
        )
        assert aircheck is not None
        assert aircheck.phone == "1-800-898-9103"


class TestResourceBackfill:
    """WP6 lockdown: thin-coverage categories are now populated."""

    def test_total_resource_count_50_plus(
        self, fw_resources: list[Resource],
    ) -> None:
        assert len(fw_resources) >= 50

    def test_safehaven_present_with_hotline(
        self, fw_resources: list[Resource],
    ) -> None:
        safe = next((r for r in fw_resources if "SafeHaven" in r.name), None)
        assert safe is not None
        assert "877-701-7233" in (safe.phone or "")

    def test_reach_disability_present(
        self, fw_resources: list[Resource],
    ) -> None:
        reach = next((r for r in fw_resources if "REACH" in r.name), None)
        assert reach is not None
        assert "817-870-9082" in (reach.phone or "")

    def test_recovery_resource_council_present(
        self, fw_resources: list[Resource],
    ) -> None:
        rrc = next(
            (r for r in fw_resources
             if "Recovery Resource Council" in r.name), None,
        )
        assert rrc is not None
        assert "817-332-6329" in (rrc.phone or "")
