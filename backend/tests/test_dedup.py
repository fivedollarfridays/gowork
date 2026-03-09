"""Tests for fuzzy deduplication of job listings."""

import pytest

from app.integrations.dedup import (
    _merge_pair,
    deduplicate_listings,
    normalize_company,
    normalize_title,
    similarity_score,
)


class TestNormalizeCompany:
    def test_strips_inc(self):
        assert normalize_company("Amazon Inc.") == "amazon"

    def test_strips_llc(self):
        assert normalize_company("Acme LLC") == "acme"

    def test_strips_corp(self):
        assert normalize_company("FedEx Corp") == "fedex"

    def test_strips_corporation(self):
        assert normalize_company("FedEx Corporation") == "fedex"

    def test_lowercases(self):
        assert normalize_company("GOODWILL") == "goodwill"

    def test_strips_whitespace(self):
        assert normalize_company("  Amazon  Inc.  ") == "amazon"

    def test_none_returns_empty(self):
        assert normalize_company(None) == ""

    def test_empty_returns_empty(self):
        assert normalize_company("") == ""


class TestNormalizeTitle:
    def test_lowercases(self):
        assert normalize_title("Warehouse Associate") == "warehouse associate"

    def test_strips_location_suffix(self):
        assert normalize_title("Driver - Montgomery, AL") == "driver"

    def test_strips_parenthetical_location(self):
        assert normalize_title("CNA (Montgomery)") == "cna"

    def test_none_returns_empty(self):
        assert normalize_title(None) == ""


class TestSimilarityScore:
    def test_identical_strings(self):
        assert similarity_score("warehouse worker", "warehouse worker") == 1.0

    def test_completely_different(self):
        assert similarity_score("warehouse worker", "brain surgeon") < 0.5

    def test_similar_titles(self):
        score = similarity_score("warehouse associate", "warehouse worker")
        assert score >= 0.5  # share "warehouse"

    def test_empty_strings(self):
        assert similarity_score("", "") == 0.0

    def test_one_empty(self):
        assert similarity_score("warehouse", "") == 0.0


class TestDeduplicateListings:
    def test_exact_duplicate_removed(self):
        listings = [
            {"title": "Warehouse Worker", "company": "Amazon", "source": "jsearch:1",
             "location": "Montgomery, AL", "description": "Pack boxes"},
            {"title": "Warehouse Worker", "company": "Amazon", "source": "brightdata:1",
             "location": "Montgomery, AL", "description": "Pack and ship boxes daily"},
        ]
        result = deduplicate_listings(listings)
        assert len(result) == 1

    def test_different_jobs_kept(self):
        listings = [
            {"title": "Warehouse Worker", "company": "Amazon", "source": "jsearch:1"},
            {"title": "Delivery Driver", "company": "FedEx", "source": "jsearch:1"},
        ]
        result = deduplicate_listings(listings)
        assert len(result) == 2

    def test_same_title_different_company_kept(self):
        listings = [
            {"title": "Warehouse Worker", "company": "Amazon", "source": "jsearch:1"},
            {"title": "Warehouse Worker", "company": "FedEx", "source": "jsearch:1"},
        ]
        result = deduplicate_listings(listings)
        assert len(result) == 2

    def test_merge_prefers_description(self):
        """When merging duplicates, prefer listing with description."""
        listings = [
            {"title": "CNA", "company": "Baptist", "source": "brightdata:1",
             "description": None},
            {"title": "CNA", "company": "Baptist", "source": "jsearch:1",
             "description": "Certified nursing assistant role"},
        ]
        result = deduplicate_listings(listings)
        assert len(result) == 1
        assert result[0]["description"] == "Certified nursing assistant role"

    def test_merge_preserves_fair_chance(self):
        """fair_chance=1 from any source should be preserved in merge."""
        listings = [
            {"title": "Driver", "company": "Goodwill", "source": "brightdata:1",
             "fair_chance": 0},
            {"title": "Driver", "company": "Goodwill", "source": "honestjobs",
             "fair_chance": 1},
        ]
        result = deduplicate_listings(listings)
        assert len(result) == 1
        assert result[0]["fair_chance"] == 1

    def test_merge_prefers_url(self):
        """Prefer listing with URL over one without."""
        listings = [
            {"title": "Cook", "company": "Dreamland", "source": "brightdata:1",
             "url": None},
            {"title": "Cook", "company": "Dreamland", "source": "honestjobs",
             "url": "https://dreamland.com/apply"},
        ]
        result = deduplicate_listings(listings)
        assert len(result) == 1
        assert result[0]["url"] == "https://dreamland.com/apply"

    def test_fuzzy_title_match(self):
        """Slight title variations for same company should dedup."""
        listings = [
            {"title": "Warehouse Associate", "company": "Amazon Inc.",
             "source": "jsearch:1"},
            {"title": "Warehouse Associate - Montgomery", "company": "Amazon",
             "source": "brightdata:1"},
        ]
        result = deduplicate_listings(listings)
        assert len(result) == 1

    def test_empty_list(self):
        assert deduplicate_listings([]) == []

    def test_single_listing(self):
        listings = [{"title": "CNA", "company": "Baptist", "source": "jsearch:1"}]
        result = deduplicate_listings(listings)
        assert len(result) == 1

    def test_preserves_source_from_winner(self):
        """Merged listing keeps source from the listing with more data."""
        listings = [
            {"title": "CNA", "company": "Baptist", "source": "brightdata:1"},
            {"title": "CNA", "company": "Baptist", "source": "jsearch:1",
             "description": "Full description here", "url": "https://apply.com"},
        ]
        result = deduplicate_listings(listings)
        assert result[0]["source"] == "jsearch:1"


class TestMergePair:
    def test_fills_missing_field_from_loser(self):
        """Winner missing location gets it filled from loser (line 66)."""
        winner = {"title": "CNA", "company": "Baptist", "description": "desc",
                  "url": "https://apply.com"}
        loser = {"title": "CNA", "company": "Baptist",
                 "location": "Montgomery, AL"}
        merged = _merge_pair(winner, loser)
        assert merged["location"] == "Montgomery, AL"

    def test_preserves_fair_chance_from_loser(self):
        """Loser with fair_chance=1 overrides winner (line 69)."""
        winner = {"title": "Driver", "company": "Goodwill",
                  "description": "Drive trucks", "url": "https://apply.com",
                  "location": "Montgomery, AL", "fair_chance": 0}
        loser = {"title": "Driver", "company": "Goodwill", "fair_chance": 1}
        merged = _merge_pair(winner, loser)
        assert merged["fair_chance"] == 1
