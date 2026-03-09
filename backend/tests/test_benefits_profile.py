"""Tests for benefits profile in assessment — T25.2."""

import json

import pytest

from app.modules.benefits.types import BenefitsProfile
from app.modules.matching.types import AssessmentRequest, BarrierType


class TestBenefitsFormDataInRequest:
    """AssessmentRequest accepts optional benefits_data."""

    def test_request_without_benefits_data(self):
        req = AssessmentRequest(
            zip_code="36104",
            employment_status="unemployed",
            barriers={BarrierType.CREDIT: True},
            work_history="test",
        )
        assert req.benefits_data is None

    def test_request_with_benefits_data(self):
        req = AssessmentRequest(
            zip_code="36104",
            employment_status="unemployed",
            barriers={BarrierType.CREDIT: True},
            work_history="test",
            benefits_data={
                "household_size": 3,
                "current_monthly_income": 800,
                "enrolled_programs": ["SNAP", "TANF"],
                "dependents_under_6": 1,
                "dependents_6_to_17": 0,
            },
        )
        assert req.benefits_data is not None
        assert req.benefits_data.household_size == 3
        assert req.benefits_data.enrolled_programs == ["SNAP", "TANF"]

    def test_benefits_data_defaults(self):
        req = AssessmentRequest(
            zip_code="36104",
            employment_status="unemployed",
            barriers={BarrierType.CREDIT: True},
            work_history="test",
            benefits_data={},
        )
        assert req.benefits_data.household_size == 1
        assert req.benefits_data.current_monthly_income == 0.0
        assert req.benefits_data.enrolled_programs == []
        assert req.benefits_data.dependents_under_6 == 0
        assert req.benefits_data.dependents_6_to_17 == 0

    def test_benefits_data_validation_household_min(self):
        with pytest.raises(Exception):
            AssessmentRequest(
                zip_code="36104",
                employment_status="unemployed",
                barriers={BarrierType.CREDIT: True},
                work_history="test",
                benefits_data={"household_size": 0},
            )

    def test_benefits_data_validation_household_max(self):
        with pytest.raises(Exception):
            AssessmentRequest(
                zip_code="36104",
                employment_status="unemployed",
                barriers={BarrierType.CREDIT: True},
                work_history="test",
                benefits_data={"household_size": 9},
            )

    def test_benefits_data_validation_negative_income(self):
        with pytest.raises(Exception):
            AssessmentRequest(
                zip_code="36104",
                employment_status="unemployed",
                barriers={BarrierType.CREDIT: True},
                work_history="test",
                benefits_data={"current_monthly_income": -100},
            )


class TestBenefitsProfileConversion:
    """BenefitsFormData converts to BenefitsProfile."""

    def test_form_data_to_profile(self):
        req = AssessmentRequest(
            zip_code="36104",
            employment_status="unemployed",
            barriers={BarrierType.CREDIT: True},
            work_history="test",
            benefits_data={
                "household_size": 4,
                "current_monthly_income": 1200,
                "enrolled_programs": ["SNAP", "Section_8"],
                "dependents_under_6": 2,
                "dependents_6_to_17": 1,
            },
        )
        profile = BenefitsProfile(**req.benefits_data.model_dump())
        assert profile.household_size == 4
        assert profile.current_monthly_income == 1200
        assert profile.enrolled_programs == ["SNAP", "Section_8"]
        assert profile.dependents_under_6 == 2
        assert profile.state == "AL"

    def test_none_benefits_data_no_profile(self):
        req = AssessmentRequest(
            zip_code="36104",
            employment_status="unemployed",
            barriers={BarrierType.CREDIT: True},
            work_history="test",
        )
        assert req.benefits_data is None


class TestBenefitsProfileSerialization:
    """Benefits profile serializes to/from JSON for session storage."""

    def test_serialize_to_json(self):
        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=800,
            enrolled_programs=["SNAP"],
            dependents_under_6=1,
        )
        json_str = profile.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["household_size"] == 3
        assert parsed["enrolled_programs"] == ["SNAP"]

    def test_deserialize_from_json(self):
        data = {
            "household_size": 3,
            "current_monthly_income": 800,
            "enrolled_programs": ["SNAP"],
            "dependents_under_6": 1,
            "dependents_6_to_17": 0,
            "state": "AL",
        }
        profile = BenefitsProfile(**data)
        assert profile.household_size == 3
        assert profile.enrolled_programs == ["SNAP"]
