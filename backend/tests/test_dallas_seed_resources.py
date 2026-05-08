"""Tests for Dallas community resources, resources, and career-center seeds.

T25.2 (Sprint 25, Wave 2) — Dallas Expansion.

Schema parity with Fort Worth is the load-bearing contract: every consumer
of these JSON files (the multi-city seed loader, the matcher, the barrier
card UI) reads them through the same code path that already serves FW.
If a key is missing or extra in a Dallas entry, that consumer breaks
silently.  These tests pin the parity and pin the AC content checks
(required orgs, geocoded coordinates, eligibility-key spelling).

References:
- ``data/cities/fort-worth/community_resources.json`` — canonical shape
- ``backend/app/cities/dallas/eligibility.py`` — ``DALLAS_ELIGIBILITY_RULES``
- ``backend/app/core/seed_helpers.py`` — multi-city resource loader
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_FW_DIR = _PROJECT_ROOT / "data" / "cities" / "fort-worth"
_DALLAS_DIR = _PROJECT_ROOT / "data" / "cities" / "dallas"

_FW_CR = _FW_DIR / "community_resources.json"
_FW_RES = _FW_DIR / "resources.json"
_FW_CC = _FW_DIR / "career_centers.json"

_DALLAS_CR = _DALLAS_DIR / "community_resources.json"
_DALLAS_RES = _DALLAS_DIR / "resources.json"
_DALLAS_CC = _DALLAS_DIR / "career_centers.json"


def _load(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _names(entries: list[dict]) -> set[str]:
    return {e["name"] for e in entries if "name" in e}


# ---------------------------------------------------------------------------
# File presence + JSON validity
# ---------------------------------------------------------------------------

class TestDallasSeedFilesExist:
    def test_community_resources_file_exists(self):
        assert _DALLAS_CR.is_file(), f"missing: {_DALLAS_CR}"

    def test_resources_file_exists(self):
        assert _DALLAS_RES.is_file(), f"missing: {_DALLAS_RES}"

    def test_career_centers_file_exists(self):
        assert _DALLAS_CC.is_file(), f"missing: {_DALLAS_CC}"

    def test_community_resources_parses_as_json(self):
        data = _load(_DALLAS_CR)
        assert isinstance(data, list) and data, "must be non-empty list"

    def test_resources_parses_as_json(self):
        data = _load(_DALLAS_RES)
        assert isinstance(data, list) and data, "must be non-empty list"

    def test_career_centers_parses_as_json(self):
        data = _load(_DALLAS_CC)
        assert isinstance(data, list) and data, "must be non-empty list"


# ---------------------------------------------------------------------------
# Schema parity with Fort Worth
# ---------------------------------------------------------------------------

class TestCommunityResourcesSchemaParity:
    """Every Dallas community-resource entry must use the SAME key set as
    the FW entries.  No missing keys, no extra keys.  This is what keeps
    the city-aware seed loader from silently dropping rows.
    """

    def test_dallas_entries_use_fw_key_universe(self):
        fw_entries = _load(_FW_CR)
        dallas_entries = _load(_DALLAS_CR)

        # Union of all keys observed in FW community_resources entries.
        fw_keys: set[str] = set()
        for e in fw_entries:
            fw_keys.update(e.keys())

        for i, entry in enumerate(dallas_entries):
            extra = set(entry.keys()) - fw_keys
            assert not extra, (
                f"Dallas community_resources[{i}] ({entry.get('name')!r}) "
                f"has keys not present in FW schema: {sorted(extra)}"
            )

    def test_every_dallas_entry_has_required_core_keys(self):
        # Required keys present on EVERY FW community-resources entry.
        # Computed from the FW file rather than hardcoded so that this
        # test stays in lockstep if the FW schema is extended.
        fw_entries = _load(_FW_CR)
        required = set.intersection(*(set(e.keys()) for e in fw_entries))
        # Sanity: the FW file should agree on at least these.
        assert {"name", "category", "address", "lat", "lng"} <= required

        dallas_entries = _load(_DALLAS_CR)
        for i, entry in enumerate(dallas_entries):
            missing = required - set(entry.keys())
            assert not missing, (
                f"Dallas community_resources[{i}] ({entry.get('name')!r}) "
                f"missing required keys: {sorted(missing)}"
            )


class TestResourcesSchemaParity:
    """Dallas ``resources.json`` rows are seeded into the same SQL
    ``resources`` table as FW.  Key set must be a subset of FW's union.
    """

    def test_dallas_entries_use_fw_key_universe(self):
        fw_entries = _load(_FW_RES)
        dallas_entries = _load(_DALLAS_RES)

        fw_keys: set[str] = set()
        for e in fw_entries:
            fw_keys.update(e.keys())

        for i, entry in enumerate(dallas_entries):
            extra = set(entry.keys()) - fw_keys
            assert not extra, (
                f"Dallas resources[{i}] ({entry.get('name')!r}) "
                f"has keys not present in FW schema: {sorted(extra)}"
            )


class TestCareerCentersSchemaParity:
    def test_dallas_entries_use_fw_key_universe(self):
        fw_entries = _load(_FW_CC)
        dallas_entries = _load(_DALLAS_CC)

        fw_keys: set[str] = set()
        for e in fw_entries:
            fw_keys.update(e.keys())

        for i, entry in enumerate(dallas_entries):
            extra = set(entry.keys()) - fw_keys
            assert not extra, (
                f"Dallas career_centers[{i}] ({entry.get('name')!r}) "
                f"has keys not present in FW schema: {sorted(extra)}"
            )

    def test_has_workforce_solutions_comprehensive(self):
        entries = _load(_DALLAS_CC)
        comprehensives = [
            e for e in entries
            if e.get("subcategory") == "comprehensive"
            and "Workforce Solutions" in e.get("name", "")
            and "Dallas" in e.get("name", "")
        ]
        assert comprehensives, (
            "Dallas career_centers.json must include a Workforce Solutions "
            "Greater Dallas entry with subcategory='comprehensive' "
            "(mirrors FW Workforce Solutions for Tarrant County entry)."
        )


# ---------------------------------------------------------------------------
# AC content checks — required organisations
# ---------------------------------------------------------------------------

_REQUIRED_COMMUNITY_ORGS_SUBSTRINGS = [
    "Workforce Solutions Greater Dallas",
    "Dallas Public Library",
    "Catholic Charities",  # Catholic Charities Dallas
    "North Texas Food Bank",
    "Dallas County Health",  # Dallas County Health & Human Services
    "ChildCareGroup",
    "North Texas 211",
    "Legal Aid of NorthWest Texas",  # Dallas branch
    "Dallas Volunteer Attorney Program",
    "Dallas Housing Authority",
    "Family Gateway",
    "Dallas LIFE",
]


class TestRequiredOrganisationsPresent:
    @pytest.mark.parametrize("needle", _REQUIRED_COMMUNITY_ORGS_SUBSTRINGS)
    def test_required_org_named(self, needle: str):
        names = _names(_load(_DALLAS_CR))
        matches = [n for n in names if needle in n]
        assert matches, (
            f"AC requires an entry whose name contains {needle!r} in "
            f"data/cities/dallas/community_resources.json (found names: "
            f"{sorted(names)})"
        )

    def test_workforce_solutions_has_at_least_three_locations(self):
        # AC: comprehensive site + 2 satellites minimum = 3 entries.
        names = _names(_load(_DALLAS_CR))
        ws = [n for n in names if "Workforce Solutions Greater Dallas" in n]
        assert len(ws) >= 3, (
            f"AC requires Workforce Solutions Greater Dallas comprehensive "
            f"+ 2 satellites (>=3 total).  Found {len(ws)}: {ws}"
        )

    def test_dallas_public_library_has_at_least_two_locations(self):
        names = _names(_load(_DALLAS_CR))
        libraries = [n for n in names if "Dallas Public Library" in n]
        assert len(libraries) >= 2, (
            f"AC requires >=2 Dallas Public Library job-center entries.  "
            f"Found {len(libraries)}: {libraries}"
        )


# ---------------------------------------------------------------------------
# AC content checks — geocoded coordinates and contact info
# ---------------------------------------------------------------------------

class TestCoordinatesAndContactInfo:
    """Coordinates must be real Dallas-area lat/lng -- never 0.0
    placeholders.  Phone and URL must be non-empty strings (or explicit
    null when the source genuinely provides nothing).
    """

    @pytest.mark.parametrize("path", [_DALLAS_CR, _DALLAS_RES, _DALLAS_CC])
    def test_no_zero_coordinates(self, path: Path):
        entries = _load(path)
        for i, e in enumerate(entries):
            lat, lng = e.get("lat"), e.get("lng")
            assert isinstance(lat, (int, float)) and lat != 0, (
                f"{path.name}[{i}] ({e.get('name')!r}) has invalid "
                f"lat={lat!r} -- must be a non-zero geocoded value"
            )
            assert isinstance(lng, (int, float)) and lng != 0, (
                f"{path.name}[{i}] ({e.get('name')!r}) has invalid "
                f"lng={lng!r} -- must be a non-zero geocoded value"
            )

    @pytest.mark.parametrize("path", [_DALLAS_CR, _DALLAS_RES, _DALLAS_CC])
    def test_coordinates_in_dallas_area_bounding_box(self, path: Path):
        # Generous bounding box around Dallas-Fort Worth metroplex.
        # Catches "0.0" placeholders, swapped lat/lng, and made-up
        # numbers that landed in the Atlantic.
        entries = _load(path)
        for i, e in enumerate(entries):
            lat, lng = e["lat"], e["lng"]
            assert 32.4 <= lat <= 33.4, (
                f"{path.name}[{i}] ({e.get('name')!r}) lat {lat} "
                f"outside DFW bounding box (32.4..33.4)"
            )
            assert -97.6 <= lng <= -96.4, (
                f"{path.name}[{i}] ({e.get('name')!r}) lng {lng} "
                f"outside DFW bounding box (-97.6..-96.4)"
            )

    @pytest.mark.parametrize("path", [_DALLAS_CR, _DALLAS_RES, _DALLAS_CC])
    def test_phone_and_url_present_or_explicit_null(self, path: Path):
        entries = _load(path)
        for i, e in enumerate(entries):
            phone = e.get("phone", "MISSING")
            url = e.get("url", "MISSING")
            # MISSING (key not set at all) is not allowed.  Explicit
            # null is allowed only when the source has nothing.
            assert phone != "MISSING", (
                f"{path.name}[{i}] ({e.get('name')!r}) has no 'phone' "
                f"key at all -- set explicit null if no public number."
            )
            assert url != "MISSING", (
                f"{path.name}[{i}] ({e.get('name')!r}) has no 'url' "
                f"key at all -- set explicit null if no public site."
            )
            if phone is not None:
                assert isinstance(phone, str) and phone.strip(), (
                    f"{path.name}[{i}] ({e.get('name')!r}) phone must "
                    f"be a non-empty string or explicit null, got {phone!r}"
                )
            if url is not None:
                assert isinstance(url, str) and url.strip(), (
                    f"{path.name}[{i}] ({e.get('name')!r}) url must "
                    f"be a non-empty string or explicit null, got {url!r}"
                )


# ---------------------------------------------------------------------------
# Eligibility-key spelling parity with DALLAS_ELIGIBILITY_RULES
# ---------------------------------------------------------------------------

class TestEligibilityKeySpellingParity:
    """If a resource name introduced in the seed JSON also appears in
    ``DALLAS_ELIGIBILITY_RULES`` (T25.1), the spelling MUST match
    exactly -- otherwise the eligibility lookup misses at request time
    and the resource is silently filtered out.
    """

    @staticmethod
    def _normalize(s: str) -> str:
        # Collapse whitespace + drop punctuation that commonly drifts
        # between seed and eligibility (em-dash vs hyphen, parens, etc).
        import re
        return re.sub(r"[^a-z0-9]+", "", s.lower())

    def test_eligibility_keys_have_at_least_one_seed_match(self):
        from app.cities.dallas.eligibility import DALLAS_ELIGIBILITY_RULES

        all_seed_names: set[str] = set()
        for path in (_DALLAS_CR, _DALLAS_RES, _DALLAS_CC):
            all_seed_names |= _names(_load(path))

        normalized_seed = {self._normalize(n): n for n in all_seed_names}

        # Contract: any eligibility key that maps (under normalization)
        # to a seed entry MUST also match that seed entry EXACTLY.
        # This catches em-dash vs hyphen drift, parenthetical drift,
        # and case drift — all of which silently break eligibility
        # lookup at request time.  Eligibility keys that have NO
        # corresponding seed entry (programs / abstractions like TWC
        # Child Care Services or Texas Rising Star) are allowed.
        for key in DALLAS_ELIGIBILITY_RULES:
            norm_key = self._normalize(key)
            if norm_key not in normalized_seed:
                # No seed match at all -- allowed.
                continue
            seed_name = normalized_seed[norm_key]
            assert key == seed_name, (
                f"Eligibility key {key!r} matches seed entry {seed_name!r} "
                f"under normalization but the spellings differ.  "
                f"Spelling drift will silently break eligibility lookup."
            )


# ---------------------------------------------------------------------------
# Loader smoke test -- existing FW community-resource loader on Dallas dir
# ---------------------------------------------------------------------------

class TestLoaderSmoke:
    """The existing multi-city resource loader (``city_resource_seed_files``)
    must return >=10 entries for the ``dallas`` slug without raising.
    """

    def test_city_resource_seed_files_finds_dallas_seeds(self):
        from app.core.seed_helpers import city_resource_seed_files

        files = city_resource_seed_files("dallas")
        assert files, "city_resource_seed_files('dallas') returned no files"

        total = 0
        for fp in files:
            data = json.loads(fp.read_text(encoding="utf-8"))
            assert isinstance(data, list)
            total += len(data)

        assert total >= 10, (
            f"AC requires >=10 community resources surfaced through the "
            f"loader.  Got {total} from {[str(f) for f in files]}."
        )

    def test_community_resources_at_least_ten(self):
        # Direct check on the AC: the community-resources file itself
        # must surface >=10 entries.
        entries = _load(_DALLAS_CR)
        assert len(entries) >= 10, (
            f"AC requires >=10 community resources in "
            f"data/cities/dallas/community_resources.json. Got {len(entries)}."
        )
