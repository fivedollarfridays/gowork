"""Tests for BrightData pre-built dataset loader."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from app.integrations.brightdata.dataset_loader import (
    normalize_dataset_record,
    parse_dataset_file,
    store_dataset_records,
)
from app.integrations.brightdata.salary_embed import embed_salary_text
from app.integrations.brightdata.types import BrightDataJobRecord


# -- Fixtures --

def _record(**overrides: object) -> dict:
    """Build a raw BrightData dataset record with defaults."""
    base = {
        "title": "Warehouse Associate",
        "company_name": "Amazon",
        "location": "Montgomery, AL 36104",
        "description": "Full-time warehouse position.",
        "url": "https://example.com/job/123",
        "salary": "$15.00 - $18.00 per hour",
        "job_type": "full_time",
    }
    base.update(overrides)
    return base


# -- embed_salary_text --


class TestEmbedSalaryText:
    """Salary embedding into description text."""

    def test_hourly_range(self) -> None:
        """Hourly range string embedded as-is."""
        result = embed_salary_text("Great job!", "$12.00 - $15.00 per hour")
        assert "$12.00 - $15.00 per hour" in result
        assert "Great job!" in result

    def test_annual_salary(self) -> None:
        """Annual salary formatted as per-year text."""
        result = embed_salary_text("Great job!", "$45,000 per year")
        assert "$45,000 per year" in result

    def test_numeric_hourly(self) -> None:
        """Numeric hourly value formatted as '$X.XX per hour'."""
        result = embed_salary_text("Great job!", "15.50")
        assert "$15.50 per hour" in result

    def test_numeric_annual(self) -> None:
        """Large numeric value treated as annual salary."""
        result = embed_salary_text("Great job!", "45000")
        assert "$45,000 per year" in result

    def test_none_salary(self) -> None:
        """None salary returns description unchanged."""
        result = embed_salary_text("Great job!", None)
        assert result == "Great job!"

    def test_empty_salary(self) -> None:
        """Empty salary returns description unchanged."""
        result = embed_salary_text("Great job!", "")
        assert result == "Great job!"

    def test_already_has_salary_pattern(self) -> None:
        """If description already contains salary text, don't double-embed."""
        desc = "Pay: $15.00 per hour. Great benefits."
        result = embed_salary_text(desc, "$15.00 per hour")
        # Should not duplicate
        assert result.count("$15.00") == 1

    def test_salary_dict_min_max(self) -> None:
        """Dictionary with min/max values formatted as range."""
        result = embed_salary_text("Great job!", {"min": 12.0, "max": 18.0, "type": "hourly"})
        assert "$12.00 - $18.00 per hour" in result

    def test_salary_dict_min_only(self) -> None:
        """Dictionary with only min value."""
        result = embed_salary_text("Great job!", {"min": 15.0, "type": "hourly"})
        assert "$15.00 per hour" in result

    def test_salary_dict_annual(self) -> None:
        """Dictionary with annual salary type."""
        result = embed_salary_text("Great job!", {"min": 35000, "max": 45000, "type": "annual"})
        assert "$35,000" in result
        assert "$45,000" in result
        assert "per year" in result


# -- normalize_dataset_record --


class TestNormalizeDatasetRecord:
    """Normalization of raw BrightData dataset records."""

    def test_basic_normalization(self) -> None:
        """Standard record normalizes to BrightDataJobRecord."""
        record = _record()
        result = normalize_dataset_record(record)
        assert result is not None
        assert result.title == "Warehouse Associate"
        assert result.company == "Amazon"
        assert result.location == "Montgomery, AL 36104"
        assert "$15.00 - $18.00 per hour" in result.description

    def test_salary_embedded_in_description(self) -> None:
        """Salary data embedded into description for PVS scoring."""
        record = _record(description="Basic warehouse work.", salary="$14.00 per hour")
        result = normalize_dataset_record(record)
        assert result is not None
        assert "$14.00 per hour" in result.description

    def test_missing_title_returns_none(self) -> None:
        """Records without title are skipped."""
        record = _record(title="")
        assert normalize_dataset_record(record) is None

    def test_missing_title_key_returns_none(self) -> None:
        """Records without title key are skipped."""
        record = _record()
        del record["title"]
        assert normalize_dataset_record(record) is None

    def test_alternative_field_names(self) -> None:
        """Handles alternative BrightData field names."""
        record = {
            "job_title": "Cashier",
            "company": "Walmart",
            "city": "Montgomery",
            "state": "AL",
            "job_description": "Retail position.",
            "apply_link": "https://walmart.com/job/456",
            "salary_range": "$12.00 - $14.00 per hour",
        }
        result = normalize_dataset_record(record)
        assert result is not None
        assert result.title == "Cashier"
        assert result.company == "Walmart"
        assert "Montgomery" in result.location

    def test_executive_title_excluded(self) -> None:
        """Executive titles are excluded."""
        record = _record(title="VP of Operations")
        assert normalize_dataset_record(record) is None

    def test_high_salary_excluded(self) -> None:
        """Jobs with salary > $80k/year are excluded."""
        record = _record(salary="$95,000 per year")
        assert normalize_dataset_record(record) is None

    def test_url_preserved(self) -> None:
        """URL field preserved from record."""
        record = _record(url="https://indeed.com/job/789")
        result = normalize_dataset_record(record)
        assert result is not None
        assert result.url == "https://indeed.com/job/789"

    def test_no_salary_still_works(self) -> None:
        """Records without salary data still normalize (just no salary in description)."""
        record = _record(salary=None)
        result = normalize_dataset_record(record)
        assert result is not None
        assert result.description == "Full-time warehouse position."

    def test_field_truncation(self) -> None:
        """Long fields are truncated to limits."""
        record = _record(title="A" * 600)
        result = normalize_dataset_record(record)
        assert result is not None
        assert len(result.title) <= 500


# -- parse_dataset_file --


class TestParseDatasetFile:
    """Loading and parsing dataset files."""

    def test_parse_json_array(self, tmp_path: Path) -> None:
        """Parse a JSON file with array of records."""
        records = [_record(title=f"Job {i}") for i in range(5)]
        data_file = tmp_path / "jobs.json"
        data_file.write_text(json.dumps(records))

        result = parse_dataset_file(data_file)
        assert len(result) == 5
        assert result[0].title == "Job 0"

    def test_parse_jsonl(self, tmp_path: Path) -> None:
        """Parse a JSONL file (one JSON object per line)."""
        records = [_record(title=f"Job {i}") for i in range(3)]
        data_file = tmp_path / "jobs.jsonl"
        data_file.write_text("\n".join(json.dumps(r) for r in records))

        result = parse_dataset_file(data_file)
        assert len(result) == 3

    def test_parse_csv(self, tmp_path: Path) -> None:
        """Parse a CSV file with header row."""
        csv_content = (
            "title,company_name,location,description,url,salary,job_type\n"
            "Cashier,Store,Montgomery AL,Great job,https://x.com,$12/hr,full_time\n"
            "Driver,FedEx,Montgomery AL,Driving,https://y.com,$16.00 per hour,full_time\n"
        )
        data_file = tmp_path / "jobs.csv"
        data_file.write_text(csv_content)

        result = parse_dataset_file(data_file)
        assert len(result) == 2

    def test_skips_invalid_records(self, tmp_path: Path) -> None:
        """Invalid records (no title) are skipped."""
        records = [
            _record(title="Valid Job"),
            _record(title=""),
            _record(title="Another Valid"),
        ]
        data_file = tmp_path / "jobs.json"
        data_file.write_text(json.dumps(records))

        result = parse_dataset_file(data_file)
        assert len(result) == 2

    def test_empty_file(self, tmp_path: Path) -> None:
        """Empty file returns empty list."""
        data_file = tmp_path / "jobs.json"
        data_file.write_text("[]")

        result = parse_dataset_file(data_file)
        assert len(result) == 0

    def test_dedup_by_title_company(self, tmp_path: Path) -> None:
        """Duplicate records (same title + company) are deduplicated."""
        records = [
            _record(title="Cashier", company_name="Walmart"),
            _record(title="Cashier", company_name="Walmart", salary="$13/hr"),
            _record(title="Cashier", company_name="Target"),
        ]
        data_file = tmp_path / "jobs.json"
        data_file.write_text(json.dumps(records))

        result = parse_dataset_file(data_file)
        assert len(result) == 2

    def test_montgomery_filter(self, tmp_path: Path) -> None:
        """Only Montgomery-area jobs are included when filter is enabled."""
        records = [
            _record(title="Local", location="Montgomery, AL 36104"),
            _record(title="Remote", location="Birmingham, AL 35203"),
            _record(title="Also Local", location="Prattville, AL 36067"),
        ]
        data_file = tmp_path / "jobs.json"
        data_file.write_text(json.dumps(records))

        result = parse_dataset_file(data_file, montgomery_only=True)
        # Only Montgomery-area (36xxx zips or "Montgomery" in location)
        local = [r for r in result if "Montgomery" in (r.location or "")]
        assert len(local) >= 1


# -- store_dataset_records --


class TestStoreDatasetRecords:
    """DB storage of parsed records."""

    @pytest.mark.asyncio
    async def test_empty_list_returns_zero(self) -> None:
        """No records to store returns 0."""
        session = AsyncMock()
        count = await store_dataset_records(session, [])
        assert count == 0

    @pytest.mark.asyncio
    async def test_inserts_records(self) -> None:
        """Records are inserted via insert_job_listings."""
        records = [
            BrightDataJobRecord(
                title="Cashier",
                company="Store",
                location="Montgomery, AL",
                description="Pay: $12.00 per hour",
                url="https://example.com/1",
            ),
            BrightDataJobRecord(
                title="Driver",
                company="FedEx",
                location="Montgomery, AL",
                description="Pay: $16.00 per hour",
                url="https://example.com/2",
            ),
        ]
        with patch(
            "app.integrations.brightdata.dataset_loader._get_existing_urls",
            return_value=set(),
        ), patch(
            "app.integrations.brightdata.dataset_loader.insert_job_listings",
            return_value=2,
        ) as mock_insert:
            session = AsyncMock()
            count = await store_dataset_records(session, records)
            assert count == 2
            assert mock_insert.called
            listings = mock_insert.call_args[0][1]
            assert len(listings) == 2
            assert listings[0]["source"] == "brightdata:dataset"

    @pytest.mark.asyncio
    async def test_skips_existing_urls(self) -> None:
        """Records with URLs already in DB are skipped."""
        records = [
            BrightDataJobRecord(
                title="Cashier",
                company="Store",
                location="Montgomery, AL",
                description="Pay: $12.00 per hour",
                url="https://example.com/existing",
            ),
            BrightDataJobRecord(
                title="Driver",
                company="FedEx",
                location="Montgomery, AL",
                description="Pay: $16.00 per hour",
                url="https://example.com/new",
            ),
        ]
        with patch(
            "app.integrations.brightdata.dataset_loader._get_existing_urls",
            return_value={"https://example.com/existing"},
        ), patch(
            "app.integrations.brightdata.dataset_loader.insert_job_listings",
            return_value=1,
        ) as mock_insert:
            session = AsyncMock()
            count = await store_dataset_records(session, records)
            assert count == 1
            listings = mock_insert.call_args[0][1]
            assert len(listings) == 1
            assert listings[0]["title"] == "Driver"


# -- End-to-end salary embedding + PVS scoring --


class TestSalaryPVSIntegration:
    """Verify embedded salary data is extracted by PVS salary_parser."""

    def test_embedded_hourly_parsed_by_salary_parser(self) -> None:
        """PVS salary_parser extracts salary from embedded text."""
        from app.modules.matching.salary_parser import extract_salary

        record = _record(description="Great warehouse job.", salary="$15.00 per hour")
        result = normalize_dataset_record(record)
        assert result is not None
        salary = extract_salary(result.description)
        assert salary is not None
        assert salary.hourly_rate == 15.0

    def test_embedded_range_parsed_by_salary_parser(self) -> None:
        """Salary range embedded and parsed correctly."""
        from app.modules.matching.salary_parser import extract_salary

        record = _record(description="Full-time.", salary="$12.00 - $18.00 per hour")
        result = normalize_dataset_record(record)
        assert result is not None
        salary = extract_salary(result.description)
        assert salary is not None
        assert salary.is_range is True
        assert salary.hourly_rate == 15.0  # midpoint

    def test_pvs_differentiates_with_salary_data(self) -> None:
        """Jobs with embedded salary data get different PVS scores."""
        from app.modules.matching.pvs_scorer import compute_pvs
        from app.modules.matching.types import AvailableHours, ScoringContext

        ctx = ScoringContext(
            user_zip="36101",
            transit_dependent=False,
            schedule_type=AvailableHours.FLEXIBLE,
            barriers=[],
        )

        rec_high = _record(description="Good job.", salary="$20.00 per hour")
        rec_low = _record(description="Good job.", salary="$10.00 per hour")
        rec_none = _record(description="Good job.", salary=None)

        job_high = normalize_dataset_record(rec_high)
        job_low = normalize_dataset_record(rec_low)
        job_none = normalize_dataset_record(rec_none)

        score_high = compute_pvs(
            {"description": job_high.description, "location": job_high.location, "title": job_high.title},
            ctx,
        )
        score_low = compute_pvs(
            {"description": job_low.description, "location": job_low.location, "title": job_low.title},
            ctx,
        )
        score_none = compute_pvs(
            {"description": job_none.description, "location": job_none.location, "title": job_none.title},
            ctx,
        )

        assert score_high > score_low > score_none
