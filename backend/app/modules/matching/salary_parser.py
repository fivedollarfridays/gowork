"""Regex-based salary extraction from job descriptions."""

import re
from dataclasses import dataclass

from app.modules.benefits.thresholds import HOURS_PER_YEAR

# Hourly range: $12.00 to $12.50 per hour, $15.50 - $20.00 per hour
_HOURLY_RANGE_RE = re.compile(
    r"\$(\d+(?:\.\d{1,2})?)\s*(?:to|-)\s*\$(\d+(?:\.\d{1,2})?)\s*(?:per\s+hour|/hr|an\s+hour)",
    re.IGNORECASE,
)

# Single hourly: $15/hr, $18.50 per hour, $12.00 an hour
_SINGLE_HOURLY_RE = re.compile(
    r"\$(\d+(?:\.\d{1,2})?)\s*(?:/hr|per\s+hour|an\s+hour)",
    re.IGNORECASE,
)

# Annual: $45,000 per year, $45K per year, $45k/year
_ANNUAL_RE = re.compile(
    r"\$(\d{1,3}(?:,\d{3})*|\d+)[kK]?\s*(?:per\s+year|/year|per\s+annum|annually)",
    re.IGNORECASE,
)


@dataclass
class SalaryInfo:
    """Parsed salary information from a job description."""

    hourly_rate: float
    annual_estimate: float
    is_range: bool
    raw_text: str


def _build_salary_from_hourly(
    hourly: float, *, is_range: bool, raw_text: str,
) -> SalaryInfo:
    """Build SalaryInfo from hourly rate."""
    return SalaryInfo(
        hourly_rate=hourly,
        annual_estimate=round(hourly * HOURS_PER_YEAR, 2),
        is_range=is_range,
        raw_text=raw_text,
    )


def _build_salary_from_annual(
    annual: float, *, is_range: bool, raw_text: str,
) -> SalaryInfo:
    """Build SalaryInfo from annual salary."""
    return SalaryInfo(
        hourly_rate=round(annual / HOURS_PER_YEAR, 2),
        annual_estimate=annual,
        is_range=is_range,
        raw_text=raw_text,
    )


def _parse_annual_amount(raw: str) -> float:
    """Parse an annual salary string like '45,000' or '45' (with K suffix)."""
    cleaned = raw.replace(",", "")
    return float(cleaned)


def extract_salary(description: str | None) -> SalaryInfo | None:
    """Extract salary from job description text.

    Returns None if no pay information found or input is empty/None.
    """
    if not description:
        return None

    # Hourly range (check before single to avoid partial match)
    match = _HOURLY_RANGE_RE.search(description)
    if match:
        low = float(match.group(1))
        high = float(match.group(2))
        midpoint = round((low + high) / 2, 2)
        return _build_salary_from_hourly(
            midpoint, is_range=True, raw_text=match.group(0),
        )

    # Single hourly rate
    match = _SINGLE_HOURLY_RE.search(description)
    if match:
        hourly = float(match.group(1))
        return _build_salary_from_hourly(
            hourly, is_range=False, raw_text=match.group(0),
        )

    # Annual salary
    match = _ANNUAL_RE.search(description)
    if match:
        raw_amount = match.group(1)
        # Check for K suffix in the matched text
        full = match.group(0)
        amount = _parse_annual_amount(raw_amount)
        if "k" in full.lower() and amount < 1000:
            amount *= 1000
        return _build_salary_from_annual(
            amount, is_range=False, raw_text=full,
        )

    return None


# -- Scoring ----------------------------------------------------------

EARNINGS_BENCHMARK = 40_000  # $40k/year = 1.0 score
UNDISCLOSED_PENALTY = 0.05   # near-disqualification for no pay info
DISCLOSED_FLOOR = 0.15       # any disclosed pay gets at least this


def score_earnings(salary: SalaryInfo | None) -> float:
    """Score 0.0-1.0 based on annual earnings estimate.

    No pay disclosed = 0.05 (penalized heavily).
    Any disclosed pay floors at 0.15 minimum.
    Capped at 1.0 for salaries >= $40k.
    """
    if salary is None:
        return UNDISCLOSED_PENALTY
    score = min(salary.annual_estimate / EARNINGS_BENCHMARK, 1.0)
    return max(score, DISCLOSED_FLOOR)
