"""Embed structured salary data into job description text.

Formats BrightData salary fields (strings, dicts) into text patterns
that the PVS salary_parser can extract.
"""

import re

from app.modules.benefits.thresholds import HOURS_PER_YEAR as _HOURS_PER_YEAR

# Salary already present in description
_HAS_SALARY_RE = re.compile(r"\$\d+(?:[.,]\d+)?", re.IGNORECASE)

# Annual salary threshold for numeric detection
_ANNUAL_THRESHOLD = 1000

# Salary extraction for exclusion check
_SALARY_AMOUNT_RE = re.compile(r"\$([\d,]+(?:\.\d+)?)")
_SALARY_ANNUAL_THRESHOLD = 80_000


def _format_salary_str(salary_str: str) -> str | None:
    """Format a string salary value for embedding into description.

    Handles: "$15.00 per hour", "$15.00 - $18.00 per hour", "$45,000 per year",
    bare numbers like "15.50" (hourly) or "45000" (annual).
    """
    if _HAS_SALARY_RE.search(salary_str):
        return salary_str
    try:
        val = float(salary_str.replace(",", ""))
    except (ValueError, TypeError):
        return None
    if val >= _ANNUAL_THRESHOLD:
        return f"${val:,.0f} per year"
    return f"${val:.2f} per hour"


def _format_salary_dict(salary: dict) -> str | None:
    """Format a dict with min/max/type into salary text."""
    sal_type = salary.get("type", "hourly")
    sal_min = salary.get("min")
    sal_max = salary.get("max")
    if sal_min is None and sal_max is None:
        return None
    if sal_type == "annual":
        if sal_min and sal_max:
            return f"${sal_min:,.0f} - ${sal_max:,.0f} per year"
        val = sal_min or sal_max
        return f"${val:,.0f} per year"
    if sal_min and sal_max:
        return f"${sal_min:.2f} - ${sal_max:.2f} per hour"
    val = sal_min or sal_max
    return f"${val:.2f} per hour"


def embed_salary_text(description: str, salary: str | dict | None) -> str:
    """Embed structured salary data into description text.

    If the description already contains the salary pattern, returns as-is
    to avoid duplication.
    """
    if not salary:
        return description

    if isinstance(salary, dict):
        formatted = _format_salary_dict(salary)
    else:
        formatted = _format_salary_str(str(salary))

    if not formatted:
        return description

    if formatted in description:
        return description

    return f"{description}\nPay: {formatted}"


def is_high_salary(salary_str: str | None) -> bool:
    """Check if salary exceeds $80k/year threshold."""
    if not salary_str:
        return False
    sal_lower = salary_str.lower()
    is_hourly = "hour" in sal_lower or "/hr" in sal_lower
    m = _SALARY_AMOUNT_RE.search(salary_str)
    if not m:
        return False
    amount = float(m.group(1).replace(",", ""))
    if is_hourly:
        amount *= _HOURS_PER_YEAR
    return amount > _SALARY_ANNUAL_THRESHOLD
