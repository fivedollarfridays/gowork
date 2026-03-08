"""Tests for resume text parsing and skill/industry extraction."""

import pytest

from app.modules.matching.resume_parser import (
    parse_resume,
    _extract_skills,
    _detect_industries,
    _detect_certifications,
    _extract_experience,
)
from app.modules.matching.resume_parser import ParsedResume


class TestExtractSkills:
    """Tests for keyword-based skill extraction."""

    def test_extracts_healthcare_keywords(self):
        text = "Worked as a CNA providing patient care at a hospital"
        skills = _extract_skills(text)
        assert "cna" in skills
        assert "patient" in skills
        assert "hospital" in skills

    def test_extracts_manufacturing_keywords(self):
        text = "Forklift certified, operated assembly lines in warehouse"
        skills = _extract_skills(text)
        assert "forklift" in skills
        assert "assembly" in skills
        assert "warehouse" in skills

    def test_extracts_transportation_keywords(self):
        text = "CDL driver with experience in delivery and trucking"
        skills = _extract_skills(text)
        assert "cdl" in skills
        assert "driver" in skills
        assert "delivery" in skills

    def test_extracts_retail_keywords(self):
        text = "Customer service associate at retail store, cashier duties"
        skills = _extract_skills(text)
        assert "cashier" in skills
        assert "retail" in skills

    def test_empty_text_returns_empty(self):
        assert _extract_skills("") == []

    def test_no_matching_keywords(self):
        text = "I enjoy hiking and reading books on weekends"
        skills = _extract_skills(text)
        assert skills == []

    def test_case_insensitive(self):
        text = "NURSE at Baptist HOSPITAL"
        skills = _extract_skills(text)
        assert "nurse" in skills
        assert "hospital" in skills

    def test_word_boundary_matching(self):
        """Should not match 'plant' inside 'plantation'."""
        text = "Worked at the manufacturing plant"
        skills = _extract_skills(text)
        assert "plant" in skills
        assert "manufacturing" in skills


class TestDetectIndustries:
    """Tests for reverse-mapping skills to industry categories."""

    def test_maps_healthcare_skills(self):
        skills = ["nurse", "patient", "hospital"]
        industries = _detect_industries(skills)
        assert "healthcare" in industries

    def test_maps_manufacturing_skills(self):
        skills = ["forklift", "warehouse", "assembly"]
        industries = _detect_industries(skills)
        assert "manufacturing" in industries

    def test_maps_multiple_industries(self):
        skills = ["nurse", "forklift", "cashier"]
        industries = _detect_industries(skills)
        assert "healthcare" in industries
        assert "manufacturing" in industries
        assert "food_service" in industries or "retail" in industries

    def test_empty_skills_returns_empty(self):
        assert _detect_industries([]) == []

    def test_deduplicates_industries(self):
        skills = ["nurse", "cna", "patient", "hospital"]
        industries = _detect_industries(skills)
        assert industries.count("healthcare") == 1


class TestDetectCertifications:
    """Tests for certification detection in resume text."""

    def test_empty_text_returns_empty(self):
        assert _detect_certifications("") == []
        assert _detect_certifications("   ") == []

    def test_detects_cna(self):
        text = "Certified Nursing Assistant (CNA) since 2019"
        certs = _detect_certifications(text)
        assert "CNA" in certs

    def test_detects_cdl(self):
        text = "Holds a valid CDL Class A license"
        certs = _detect_certifications(text)
        assert "CDL" in certs

    def test_detects_lpn(self):
        text = "Licensed Practical Nurse LPN training completed"
        certs = _detect_certifications(text)
        assert "LPN" in certs

    def test_detects_ged(self):
        text = "Earned GED in 2020"
        certs = _detect_certifications(text)
        assert "GED" in certs

    def test_detects_multiple_certifications(self):
        text = "CNA and CDL certified, completed GED program"
        certs = _detect_certifications(text)
        assert "CNA" in certs
        assert "CDL" in certs
        assert "GED" in certs

    def test_no_certifications(self):
        text = "Worked at retail store for three years"
        certs = _detect_certifications(text)
        assert certs == []

    def test_case_insensitive(self):
        text = "cna certified driver with cdl"
        certs = _detect_certifications(text)
        assert "CNA" in certs
        assert "CDL" in certs

    def test_word_boundary(self):
        """Should not match 'CDL' inside 'ACDLA'."""
        text = "Worked at ACDLA organization"
        certs = _detect_certifications(text)
        assert "CDL" not in certs


class TestExtractExperience:
    """Tests for job title/role extraction."""

    def test_extracts_common_titles(self):
        text = "Worked as cashier at Walmart and warehouse associate at Amazon"
        exp = _extract_experience(text)
        assert "cashier" in exp
        assert "warehouse" in exp

    def test_extracts_healthcare_titles(self):
        text = "Nurse aide providing patient care in clinic setting"
        exp = _extract_experience(text)
        assert "nurse" in exp

    def test_empty_text(self):
        assert _extract_experience("") == []


class TestParseResume:
    """Tests for the main parse_resume function."""

    def test_full_resume_parsing(self):
        text = (
            "Jane Smith - Montgomery, AL\n"
            "Certified Nursing Assistant (CNA) with 3 years experience.\n"
            "Worked at Baptist Medical Center providing patient care.\n"
            "Also have CDL license for transportation work.\n"
            "Skills: forklift operation, customer service, cashier."
        )
        result = parse_resume(text)

        assert isinstance(result, ParsedResume)
        assert result.word_count > 0
        assert "CNA" in result.certifications
        assert "CDL" in result.certifications
        assert "healthcare" in result.industries
        assert len(result.skills) > 0

    def test_empty_text(self):
        result = parse_resume("")
        assert result.skills == []
        assert result.industries == []
        assert result.certifications == []
        assert result.experience_keywords == []
        assert result.word_count == 0

    def test_short_text(self):
        result = parse_resume("hi")
        assert result.word_count == 1

    def test_whitespace_only(self):
        result = parse_resume("   \n\t  ")
        assert result.word_count == 0

    def test_returns_parsed_resume_type(self):
        result = parse_resume("warehouse worker")
        assert isinstance(result, ParsedResume)
        assert "warehouse" in result.skills
        assert "manufacturing" in result.industries
