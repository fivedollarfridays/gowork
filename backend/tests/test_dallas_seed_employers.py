"""Tests for the Dallas employer index — Sprint 25 / T25.3.

Pins the schema parity, minimum entry counts, and FW non-duplication
contract for the three Dallas seed files added in this task:

* ``data/cities/dallas/employers.json`` (>=30 entries)
* ``data/cities/dallas/employer_policies_seed.json`` (mirrors FW shape)
* ``backend/data/cities/dallas/honestjobs_listings.json`` (>=15 entries)

Also smoke-checks the JobAggregator wire-up: ``honestjobs`` must now be
listed in ``cities/dallas.yaml`` so the city-aware aggregator path picks
up the new seed file.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.cities.config import load_city_config


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DALLAS_DATA_DIR = REPO_ROOT / "data" / "cities" / "dallas"
FW_DATA_DIR = REPO_ROOT / "data" / "cities" / "fort-worth"
DALLAS_BACKEND_DIR = REPO_ROOT / "backend" / "data" / "cities" / "dallas"
FW_BACKEND_DIR = REPO_ROOT / "backend" / "data" / "cities" / "fort-worth"


REQUIRED_EMPLOYER_KEYS = {
    "name",
    "category",
    "lat",
    "lng",
    "address",
    "phone",
    "url",
    "fair_chance",
    "background_check_timing",
}


def _load_json(path: Path) -> list[dict]:
    """Read a JSON file as UTF-8, returning a list of dicts."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class TestDallasEmployersSeed:
    def test_employers_file_exists(self):
        path = DALLAS_DATA_DIR / "employers.json"
        assert path.exists(), f"missing {path}"

    def test_employers_parse_clean_utf8(self):
        path = DALLAS_DATA_DIR / "employers.json"
        # Round-trip raw bytes through utf-8 to confirm encoding.
        raw = path.read_bytes()
        decoded = raw.decode("utf-8")
        data = json.loads(decoded)
        assert isinstance(data, list)
        assert all(isinstance(rec, dict) for rec in data)

    def test_at_least_30_employers(self):
        employers = _load_json(DALLAS_DATA_DIR / "employers.json")
        assert len(employers) >= 30, (
            f"AC requires >=30 Dallas employers, got {len(employers)}"
        )

    def test_every_employer_has_required_keys(self):
        employers = _load_json(DALLAS_DATA_DIR / "employers.json")
        for emp in employers:
            missing = REQUIRED_EMPLOYER_KEYS - set(emp.keys())
            assert not missing, (
                f"employer {emp.get('name')!r} missing keys: {sorted(missing)}"
            )

    def test_schema_parity_within_dallas(self):
        # Every Dallas employer entry has the SAME key set as every other
        # Dallas entry (uniform shape).  The FW employers.json shape is
        # leaner (id/name/industry/location/fair_chance/notes); Dallas
        # uses the richer Sprint 25 schema with coords + contact.  This
        # test pins uniformity *within* the Dallas seed.
        employers = _load_json(DALLAS_DATA_DIR / "employers.json")
        assert employers, "employers.json must not be empty"
        canonical = set(employers[0].keys())
        for emp in employers[1:]:
            assert set(emp.keys()) == canonical, (
                f"employer {emp.get('name')!r} key set diverges: "
                f"{sorted(set(emp.keys()) ^ canonical)}"
            )

    def test_fair_chance_is_bool(self):
        employers = _load_json(DALLAS_DATA_DIR / "employers.json")
        for emp in employers:
            assert isinstance(emp["fair_chance"], bool), (
                f"{emp['name']!r}: fair_chance must be bool, got {type(emp['fair_chance']).__name__}"
            )

    def test_lat_lng_in_dfw_metro_box(self):
        # Sanity-check that no invented coordinates slipped in.  DFW
        # metro sits roughly inside lat 32.5..33.3, lng -97.6..-96.4.
        employers = _load_json(DALLAS_DATA_DIR / "employers.json")
        for emp in employers:
            lat = emp["lat"]
            lng = emp["lng"]
            assert isinstance(lat, (int, float)) and isinstance(lng, (int, float))
            assert 32.5 <= lat <= 33.3, f"{emp['name']!r}: lat {lat} outside DFW box"
            assert -97.6 <= lng <= -96.4, f"{emp['name']!r}: lng {lng} outside DFW box"

    def test_no_duplicate_name_address_with_fw(self):
        # Cross-file (name, address) intersection must be empty.  FW
        # employers.json doesn't carry "address" — fall back to
        # (name, location) when address is missing on the FW side.
        dallas = _load_json(DALLAS_DATA_DIR / "employers.json")
        fw = _load_json(FW_DATA_DIR / "employers.json")
        dallas_keys = {(e["name"].strip(), e["address"].strip()) for e in dallas}
        fw_keys = {
            (e["name"].strip(), (e.get("address") or e.get("location") or "").strip())
            for e in fw
        }
        overlap = dallas_keys & fw_keys
        assert not overlap, f"name+address dupes between FW and Dallas: {overlap}"

    def test_includes_fair_chance_and_general_mix(self):
        # AC: "mixed reentry-friendly + general".  Require >=1 of each.
        employers = _load_json(DALLAS_DATA_DIR / "employers.json")
        fc = [e for e in employers if e["fair_chance"]]
        non_fc = [e for e in employers if not e["fair_chance"]]
        assert len(fc) >= 1, "no fair-chance employers in Dallas seed"
        assert len(non_fc) >= 1, "no general (non-fair-chance) employers in Dallas seed"


class TestDallasEmployerPoliciesSeed:
    FW_POLICY_KEYS = {
        "employer_name",
        "fair_chance",
        "excluded_charges",
        "lookback_years",
        "bg_check_timing",
        "industry",
        "source",
        "montgomery_area",
    }

    def test_policies_file_exists(self):
        path = DALLAS_DATA_DIR / "employer_policies_seed.json"
        assert path.exists(), f"missing {path}"

    def test_policies_parse_clean_utf8(self):
        path = DALLAS_DATA_DIR / "employer_policies_seed.json"
        decoded = path.read_bytes().decode("utf-8")
        data = json.loads(decoded)
        assert isinstance(data, list)
        assert all(isinstance(rec, dict) for rec in data)

    def test_policies_mirror_fw_schema(self):
        records = _load_json(DALLAS_DATA_DIR / "employer_policies_seed.json")
        assert records, "employer_policies_seed.json must not be empty"
        for rec in records:
            assert set(rec.keys()) == self.FW_POLICY_KEYS, (
                f"policy {rec.get('employer_name')!r} key set diverges: "
                f"{sorted(set(rec.keys()) ^ self.FW_POLICY_KEYS)}"
            )

    def test_bg_check_timing_values_valid(self):
        records = _load_json(DALLAS_DATA_DIR / "employer_policies_seed.json")
        for rec in records:
            assert rec["bg_check_timing"] in {"pre_offer", "post_offer"}


class TestDallasHonestJobsSeed:
    def test_honestjobs_file_exists(self):
        path = DALLAS_BACKEND_DIR / "honestjobs_listings.json"
        assert path.exists(), f"missing {path}"

    def test_honestjobs_parse_clean_utf8(self):
        path = DALLAS_BACKEND_DIR / "honestjobs_listings.json"
        decoded = path.read_bytes().decode("utf-8")
        data = json.loads(decoded)
        assert isinstance(data, list)
        assert all(isinstance(rec, dict) for rec in data)

    def test_at_least_15_dallas_listings(self):
        listings = _load_json(DALLAS_BACKEND_DIR / "honestjobs_listings.json")
        assert len(listings) >= 15, (
            f"AC requires >=15 Dallas honestjobs listings, got {len(listings)}"
        )

    def test_honestjobs_records_match_seed_loader_shape(self):
        # Mirror app.integrations.honestjobs.seed._row_from_record:
        # title (required), company/location/description/url/scraped_at
        # /fair_chance/lat/lng all consumed.
        listings = _load_json(DALLAS_BACKEND_DIR / "honestjobs_listings.json")
        for rec in listings:
            assert "title" in rec and rec["title"], "title required by seeder"
            assert "company" in rec
            assert "location" in rec
            assert "url" in rec
            assert rec.get("source") == "honestjobs"
            assert rec.get("fair_chance") in (0, 1), (
                f"{rec.get('title')!r}: fair_chance must be 0 or 1 (sqlite int)"
            )

    def test_no_duplicate_with_fw_honestjobs(self):
        # AC: FW honestjobs entries already tagged DFW remain in FW seed;
        # do not duplicate.  Dedupe key must match the seeder's (title,
        # company) tuple — that's how seed_honestjobs_listings filters.
        dallas = _load_json(DALLAS_BACKEND_DIR / "honestjobs_listings.json")
        fw = _load_json(FW_BACKEND_DIR / "honestjobs_listings.json")
        dallas_keys = {(rec.get("title"), rec.get("company")) for rec in dallas}
        fw_keys = {(rec.get("title"), rec.get("company")) for rec in fw}
        overlap = dallas_keys & fw_keys
        assert not overlap, f"(title, company) dupes between FW and Dallas: {overlap}"

    def test_listings_mention_dallas_or_dfw_metro(self):
        # AC: ">=15 Dallas-specific listings".  Confirm location strings
        # actually point at Dallas or a Dallas-side suburb (Plano,
        # Garland, Irving, Richardson, Mesquite, Carrollton, Grand
        # Prairie, Addison).  FW / Arlington entries belong in FW seed.
        dallas_side = {
            "dallas",
            "plano",
            "garland",
            "irving",
            "richardson",
            "mesquite",
            "carrollton",
            "grand prairie",
            "addison",
            "desoto",
            "duncanville",
            "lancaster",
        }
        listings = _load_json(DALLAS_BACKEND_DIR / "honestjobs_listings.json")
        for rec in listings:
            location = (rec.get("location") or "").lower()
            assert any(city in location for city in dallas_side), (
                f"{rec.get('title')!r} location {location!r} not Dallas-side"
            )


class TestDallasYamlAdapterWiring:
    def test_dallas_job_adapters_includes_honestjobs(self):
        # Cache-clear because other tests may have already loaded
        # dallas.yaml under the pre-T25.3 (no honestjobs) state.
        load_city_config.cache_clear()
        cfg = load_city_config("dallas")
        assert "honestjobs" in cfg.job_adapters

    def test_dallas_job_adapters_full_set(self):
        load_city_config.cache_clear()
        cfg = load_city_config("dallas")
        assert cfg.job_adapters == ["twc", "usajobs", "honestjobs"]

    def test_data_dir_resolves_dallas_honestjobs_seed(self):
        # JobAggregator smoke check: city.data_dir + honestjobs_listings
        # filename must resolve to a real file on disk.  This is the
        # exact path the aggregator uses to locate per-city seeds.
        load_city_config.cache_clear()
        cfg = load_city_config("dallas")
        listings_path = REPO_ROOT / "backend" / cfg.data_dir / "honestjobs_listings.json"
        assert listings_path.exists(), (
            f"city data_dir {cfg.data_dir!r} does not resolve to a "
            f"honestjobs seed at {listings_path}"
        )
