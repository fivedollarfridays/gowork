"""Query helpers for criminal record module — employer policies and profiles."""

import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.criminal.employer_policy import EmployerPolicy


def _row_to_employer_policy(data: dict) -> EmployerPolicy:
    """Convert a DB row dict to an EmployerPolicy model."""
    return EmployerPolicy(
        employer_name=data["employer_name"],
        fair_chance=bool(data["fair_chance"]),
        excluded_charges=json.loads(data["excluded_charges"]),
        lookback_years=data["lookback_years"],
        background_check_timing=data["bg_check_timing"],
        industry=data["industry"],
        source=data["source"],
        montgomery_area=bool(data["montgomery_area"]),
    )


async def get_all_employer_policies(
    session: AsyncSession,
) -> list[EmployerPolicy]:
    """Fetch all employer policies from DB."""
    result = await session.execute(text("SELECT * FROM employer_policies"))
    return [_row_to_employer_policy(dict(row._mapping)) for row in result]


async def get_employer_policy_by_name(
    session: AsyncSession, employer_name: str,
) -> EmployerPolicy | None:
    """Fetch a single employer policy by name, or None."""
    result = await session.execute(
        text("SELECT * FROM employer_policies WHERE employer_name = :name"),
        {"name": employer_name},
    )
    row = result.first()
    if row is None:
        return None
    return _row_to_employer_policy(dict(row._mapping))
