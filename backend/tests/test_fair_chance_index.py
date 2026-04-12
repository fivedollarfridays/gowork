"""Tests for fair-chance employer index."""

import json
import pytest
from pathlib import Path


class TestFairChanceIndex:
    def test_load_fort_worth_employers(self):
        from app.modules.criminal.fair_chance_index import load_employers

        employers = load_employers("fort-worth")
        assert len(employers) > 0

    def test_fair_chance_filter(self):
        from app.modules.criminal.fair_chance_index import get_fair_chance_employers

        employers = get_fair_chance_employers("fort-worth")
        for emp in employers:
            assert emp["fair_chance"] is True

    def test_fair_chance_count(self):
        from app.modules.criminal.fair_chance_index import get_fair_chance_employers

        employers = get_fair_chance_employers("fort-worth")
        assert len(employers) >= 5  # At least 5 fair-chance employers

    def test_unknown_city_returns_empty(self):
        from app.modules.criminal.fair_chance_index import load_employers

        employers = load_employers("nonexistent-city")
        assert employers == []
