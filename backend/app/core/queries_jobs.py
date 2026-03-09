"""Async query helpers for job_listings table."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_all_job_listings(session: AsyncSession) -> list[dict]:
    """Fetch all job listings."""
    result = await session.execute(text("SELECT * FROM job_listings"))
    return [dict(row._mapping) for row in result]


async def get_job_listing_by_id(session: AsyncSession, job_id: int) -> dict | None:
    """Fetch a single job listing by id."""
    result = await session.execute(
        text("SELECT * FROM job_listings WHERE id = :id"),
        {"id": job_id},
    )
    row = result.first()
    return dict(row._mapping) if row else None


async def insert_job_listings(session: AsyncSession, listings: list[dict]) -> int:
    """Bulk insert job listings. Returns count inserted."""
    if not listings:
        return 0
    params = [
        {
            "title": row["title"],
            "company": row.get("company"),
            "location": row.get("location"),
            "description": row.get("description"),
            "url": row.get("url"),
            "source": row.get("source"),
            "scraped_at": row["scraped_at"],
            "expires_at": row.get("expires_at"),
            "credit_check": row.get("credit_check", "unknown"),
            "fair_chance": row.get("fair_chance", 0),
        }
        for row in listings
    ]
    await session.execute(
        text(
            "INSERT INTO job_listings (title, company, location, description, url, source, scraped_at, expires_at, credit_check, fair_chance) "
            "VALUES (:title, :company, :location, :description, :url, :source, :scraped_at, :expires_at, :credit_check, :fair_chance)"
        ),
        params,
    )
    await session.commit()
    return len(listings)


async def get_job_listings_by_source(session: AsyncSession, source: str) -> list[dict]:
    """Fetch job listings filtered by source."""
    result = await session.execute(
        text("SELECT * FROM job_listings WHERE source = :source"),
        {"source": source},
    )
    return [dict(row._mapping) for row in result]
