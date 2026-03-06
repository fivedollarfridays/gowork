"""Tests for resource affinity routing in the matching engine."""

import uuid
from unittest.mock import patch

import pytest

from app.modules.matching.affinity import (
    BARRIER_PROCESSING_ORDER,
    CAREER_CENTER_STEP,
    RESOURCE_AFFINITY,
)
from app.modules.matching.engine import _build_barrier_cards, _build_next_steps
from app.modules.matching.types import (
    BarrierSeverity,
    BarrierType,
    EmploymentStatus,
    Resource,
    UserProfile,
)


def _make_profile(**overrides) -> UserProfile:
    defaults = {
        "session_id": str(uuid.uuid4()),
        "zip_code": "36104",
        "employment_status": EmploymentStatus.UNEMPLOYED,
        "barrier_count": 3,
        "primary_barriers": [
            BarrierType.CREDIT,
            BarrierType.TRANSPORTATION,
            BarrierType.CHILDCARE,
        ],
        "barrier_severity": BarrierSeverity.MEDIUM,
        "needs_credit_assessment": True,
        "transit_dependent": True,
        "schedule_type": "daytime",
        "work_history": "Former CNA at Baptist Hospital",
        "target_industries": ["healthcare"],
    }
    defaults.update(overrides)
    return UserProfile(**defaults)


def _make_resource(**overrides) -> Resource:
    defaults = {"id": 1, "name": "Generic Resource", "category": "career_center"}
    defaults.update(overrides)
    return Resource(**defaults)


class TestBarrierProcessingOrder:
    def test_order_has_specialized_barriers_first(self):
        """Specialized barriers (transportation, childcare, training) come first."""
        order = BARRIER_PROCESSING_ORDER
        trans_idx = order.index(BarrierType.TRANSPORTATION)
        child_idx = order.index(BarrierType.CHILDCARE)
        train_idx = order.index(BarrierType.TRAINING)
        credit_idx = order.index(BarrierType.CREDIT)
        assert trans_idx < credit_idx
        assert child_idx < credit_idx
        assert train_idx < credit_idx

    def test_order_contains_all_barrier_types(self):
        """Processing order should cover all BarrierType values."""
        for bt in BarrierType:
            assert bt in BARRIER_PROCESSING_ORDER


class TestResourceAffinity:
    def test_affinity_map_has_transit_entries(self):
        """MATS and transit keywords map to transportation."""
        for keyword in ["mats", "montgomery area transit"]:
            assert RESOURCE_AFFINITY[keyword] == BarrierType.TRANSPORTATION

    def test_affinity_map_has_childcare_entries(self):
        """DHR and childcare keywords map to childcare."""
        for keyword in ["dhr", "department of human resources", "childcare"]:
            assert RESOURCE_AFFINITY[keyword] == BarrierType.CHILDCARE

    def test_affinity_map_has_training_entries(self):
        """MRWTC and training keywords map to training."""
        for keyword in ["mrwtc", "montgomery regional workforce", "workforce training"]:
            assert RESOURCE_AFFINITY[keyword] == BarrierType.TRAINING


class TestAffinityRouting:
    def test_mats_on_transportation_card(self):
        """MATS should appear on transportation card, not credit."""
        profile = _make_profile(
            primary_barriers=[BarrierType.CREDIT, BarrierType.TRANSPORTATION],
        )
        resources = [
            _make_resource(id=1, name="MATS Transit Center", category="career_center"),
            _make_resource(id=2, name="Credit Counseling", category="social_service"),
        ]
        cards = _build_barrier_cards(profile, resources)
        trans_card = next(c for c in cards if c.type == BarrierType.TRANSPORTATION)
        credit_card = next(c for c in cards if c.type == BarrierType.CREDIT)
        assert any(r.name == "MATS Transit Center" for r in trans_card.resources)
        assert not any(r.name == "MATS Transit Center" for r in credit_card.resources)

    def test_dhr_on_childcare_card(self):
        """DHR should appear on childcare card."""
        profile = _make_profile(
            primary_barriers=[BarrierType.CREDIT, BarrierType.CHILDCARE],
        )
        resources = [
            _make_resource(id=1, name="DHR Childcare Services", category="childcare"),
        ]
        cards = _build_barrier_cards(profile, resources)
        childcare_card = next(c for c in cards if c.type == BarrierType.CHILDCARE)
        assert any(r.name == "DHR Childcare Services" for r in childcare_card.resources)

    def test_mrwtc_on_training_card(self):
        """MRWTC should appear on training card."""
        profile = _make_profile(
            primary_barriers=[BarrierType.CREDIT, BarrierType.TRAINING],
        )
        resources = [
            _make_resource(
                id=1, name="Montgomery Regional Workforce Training Center",
                category="training",
            ),
        ]
        cards = _build_barrier_cards(profile, resources)
        training_card = next(c for c in cards if c.type == BarrierType.TRAINING)
        assert any(
            "Montgomery Regional Workforce" in r.name
            for r in training_card.resources
        )

    def test_career_center_excluded_from_barrier_cards(self):
        """Montgomery Career Center should not appear in any barrier card."""
        profile = _make_profile(
            primary_barriers=[BarrierType.CREDIT, BarrierType.TRANSPORTATION],
        )
        resources = [
            _make_resource(id=1, name="Montgomery Career Center", category="career_center"),
            _make_resource(id=2, name="Other Service", category="social_service"),
        ]
        cards = _build_barrier_cards(profile, resources)
        for card in cards:
            assert not any(
                "career center" in r.name.lower() for r in card.resources
            ), f"Career Center found on {card.type} card"

    def test_career_center_in_next_steps(self):
        """Career Center should be first in immediate_next_steps."""
        profile = _make_profile(
            primary_barriers=[BarrierType.CREDIT],
        )
        resources = [
            _make_resource(id=1, name="Montgomery Career Center", category="career_center"),
        ]
        cards = _build_barrier_cards(profile, resources)
        steps = _build_next_steps(profile, cards)
        assert steps[0] == CAREER_CENTER_STEP

    def test_maria_persona_affinity(self):
        """Maria: credit + transportation + childcare — each resource on correct card."""
        profile = _make_profile(
            primary_barriers=[
                BarrierType.CREDIT,
                BarrierType.TRANSPORTATION,
                BarrierType.CHILDCARE,
            ],
        )
        resources = [
            _make_resource(id=1, name="Montgomery Career Center", category="career_center"),
            _make_resource(id=2, name="MATS Transit Center", category="career_center"),
            _make_resource(id=3, name="DHR Childcare Services", category="childcare"),
            _make_resource(id=4, name="Credit Counseling", category="social_service"),
        ]
        cards = _build_barrier_cards(profile, resources)

        trans_card = next(c for c in cards if c.type == BarrierType.TRANSPORTATION)
        child_card = next(c for c in cards if c.type == BarrierType.CHILDCARE)
        credit_card = next(c for c in cards if c.type == BarrierType.CREDIT)

        # MATS on transportation, not credit
        assert any(r.name == "MATS Transit Center" for r in trans_card.resources)
        assert not any(r.name == "MATS Transit Center" for r in credit_card.resources)

        # DHR on childcare
        assert any(r.name == "DHR Childcare Services" for r in child_card.resources)

        # Credit Counseling on credit
        assert any(r.name == "Credit Counseling" for r in credit_card.resources)

        # Career Center on none
        for card in cards:
            assert not any(
                r.name == "Montgomery Career Center" for r in card.resources
            )

    def test_barrier_cards_preserve_user_barrier_order(self):
        """Barrier cards should be returned in the user's barrier order."""
        profile = _make_profile(
            primary_barriers=[
                BarrierType.CREDIT,
                BarrierType.TRANSPORTATION,
                BarrierType.CHILDCARE,
            ],
        )
        cards = _build_barrier_cards(profile, [])
        card_types = [c.type for c in cards]
        assert card_types == [
            BarrierType.CREDIT,
            BarrierType.TRANSPORTATION,
            BarrierType.CHILDCARE,
        ]
