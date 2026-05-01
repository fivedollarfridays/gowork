"""Stage-2: Resource ``barrier_affinity`` field powers contextual surfacing.

Tests:
1. A resource with ``barrier_affinity=["transportation"]`` is routed
   to the TRANSPORTATION card even if its name lacks the legacy
   keyword (``trinity metro``).
2. A multi-tag resource (``["transportation", "criminal_record"]``)
   surfaces on BOTH cards when the user has both barriers.
3. ``score_resource`` awards 1.0 barrier alignment to resources whose
   ``barrier_affinity`` overlaps the user's barriers, even when the
   category falls outside the legacy ``BARRIER_CATEGORY_MAP`` set.
"""

from __future__ import annotations

from app.modules.matching.affinity import (
    assign_resources,
    get_affinity_barrier,
    get_affinity_barriers,
)
from app.modules.matching.scoring import score_resource
from app.modules.matching.types import (
    AvailableHours,
    BarrierSeverity,
    BarrierType,
    EmploymentStatus,
    Resource,
    UserProfile,
)


def _twc_transport_voucher() -> Resource:
    """A TWC slice that doesn't trigger the legacy 'workforce' keyword."""
    return Resource(
        id=901,
        name="TWC Transportation Vouchers - Tarrant County",
        category="social_service",
        subcategory="vouchers",
        address="1200 Circle Dr, Fort Worth, TX 76119",
        phone="817-413-4400",
        url="https://www.workforcesolutions.net/transportation",
        services=["gas_cards", "bus_passes"],
        notes="TWC transportation vouchers for active jobseekers.",
        barrier_affinity=["transportation"],
    )


def _multi_tag_voucher() -> Resource:
    """Catholic-Charities-style resource that serves multiple barriers."""
    return Resource(
        id=902,
        name="Catholic Charities Fort Worth - Auto + Reentry Aid",
        category="social_service",
        subcategory="vouchers",
        address="249 W Thornhill Dr, Fort Worth, TX 76115",
        phone="817-534-0814",
        url="https://catholiccharitiesfortworth.org",
        services=["car_repair", "gas_vouchers", "reentry_case_management"],
        barrier_affinity=["transportation", "criminal_record"],
    )


def _user_profile(barriers: list[BarrierType]) -> UserProfile:
    return UserProfile(
        session_id="t",
        zip_code="76102",
        employment_status=EmploymentStatus.UNEMPLOYED,
        barrier_count=len(barriers),
        primary_barriers=barriers,
        barrier_severity=BarrierSeverity.LOW,
        needs_credit_assessment=False,
        transit_dependent=True,
        schedule_type=AvailableHours.DAYTIME,
        work_history="",
        target_industries=[],
    )


class TestBarrierAffinityField:
    def test_explicit_tag_resolves_to_barrier(self) -> None:
        r = _twc_transport_voucher()
        assert get_affinity_barrier(r) == BarrierType.TRANSPORTATION

    def test_multi_tag_returns_all_barriers(self) -> None:
        r = _multi_tag_voucher()
        result = set(get_affinity_barriers(r))
        assert result == {
            BarrierType.TRANSPORTATION,
            BarrierType.CRIMINAL_RECORD,
        }

    def test_unknown_tag_is_dropped(self) -> None:
        r = Resource(
            id=903, name="Test", category="social_service",
            barrier_affinity=["transportation", "imaginary_barrier"],
        )
        result = get_affinity_barriers(r)
        assert BarrierType.TRANSPORTATION in result
        assert len(result) == 1


class TestAssignResourcesByAffinity:
    def test_transportation_voucher_lands_on_transportation_card(
        self,
    ) -> None:
        voucher = _twc_transport_voucher()
        cards = assign_resources(
            {BarrierType.TRANSPORTATION}, [voucher],
        )
        assert voucher in cards[BarrierType.TRANSPORTATION]

    def test_multi_tag_resource_appears_on_both_cards(self) -> None:
        voucher = _multi_tag_voucher()
        cards = assign_resources(
            {BarrierType.TRANSPORTATION, BarrierType.CRIMINAL_RECORD},
            [voucher],
        )
        assert voucher in cards[BarrierType.TRANSPORTATION]
        assert voucher in cards[BarrierType.CRIMINAL_RECORD]

    def test_explicit_tag_beats_legacy_keyword_route(self) -> None:
        """A 'workforce' resource explicitly tagged transportation wins
        over its legacy training-keyword routing."""
        r = Resource(
            id=904,
            name="Workforce Solutions for Tarrant County - Bus Passes",
            category="social_service",
            barrier_affinity=["transportation"],
        )
        cards = assign_resources(
            {BarrierType.TRANSPORTATION, BarrierType.TRAINING}, [r],
        )
        assert r in cards[BarrierType.TRANSPORTATION]
        assert r not in cards[BarrierType.TRAINING]


class TestScoreResourceBoostFromAffinity:
    def test_score_awards_full_alignment_on_explicit_tag(self) -> None:
        """A health-tagged resource in 'social_service' must score 1.0
        on barrier alignment for a HEALTH-barrier user."""
        r = Resource(
            id=905,
            name="REACH Independent Living - Disability Services",
            category="social_service",
            subcategory="disability",
            lat=32.7555, lng=-97.3308,
            barrier_affinity=["health"],
        )
        profile = _user_profile([BarrierType.HEALTH])
        # Score is the full PVS — must be > 0.55 (high alignment + nominal proximity)
        score = score_resource(r, profile)
        assert score >= 0.55, f"Score too low for tagged health resource: {score}"
