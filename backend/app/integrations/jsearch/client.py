"""Async HTTP client for JSearch API via RapidAPI."""

import logging

import httpx

from app.integrations.jsearch.cache import build_location, normalize_period
from app.integrations.jsearch.types import (
    JSearchAPIError,
    JSearchConfigError,
    JSearchJobRecord,
    JSearchResponse,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://jsearch.p.rapidapi.com"
_RATE_LIMIT_WARN = 0.9  # warn at 90% of monthly limit


class JSearchClient:
    """Typed async wrapper around the JSearch RapidAPI."""

    def __init__(
        self,
        api_key: str,
        host: str = "jsearch.p.rapidapi.com",
        monthly_limit: int = 200,
    ):
        if not api_key:
            raise JSearchConfigError("JSEARCH_API_KEY is not set")
        self._api_key = api_key
        self._host = host
        self._monthly_limit = monthly_limit
        self._request_count = 0
        self._http = httpx.AsyncClient(
            headers={
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": host,
            },
            timeout=30.0,
        )

    @property
    def request_count(self) -> int:
        return self._request_count

    async def search_jobs(
        self,
        query: str = "jobs",
        location: str = "Montgomery, AL",
        radius: int = 25,
        page: int = 1,
    ) -> JSearchResponse:
        """Search for jobs. Returns empty response on network errors."""
        try:
            resp = await self._http.get(
                f"{BASE_URL}/search",
                params={
                    "query": f"{query} in {location}",
                    "num_pages": str(page),
                    "radius": str(radius),
                },
            )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.warning("JSearch API unavailable: %s", exc)
            return JSearchResponse(status="ERROR", request_id="", data=[])

        self._request_count += 1
        self._check_rate_limit()

        if resp.status_code != 200:
            self._raise_api_error(resp)

        body = resp.json()
        records = [self._parse_record(r) for r in body.get("data", [])]
        return JSearchResponse(
            status=body.get("status", "OK"),
            request_id=body.get("request_id", ""),
            data=[r for r in records if r is not None],
        )

    def _parse_record(self, raw: dict) -> JSearchJobRecord | None:
        """Parse a single JSearch API record into a typed record."""
        title = raw.get("job_title")
        if not title:
            return None
        location = build_location(raw.get("job_city"), raw.get("job_state"))
        return JSearchJobRecord(
            title=title,
            company=raw.get("employer_name"),
            location=location,
            description=raw.get("job_description"),
            url=raw.get("job_apply_link"),
            salary_min=raw.get("job_min_salary"),
            salary_max=raw.get("job_max_salary"),
            salary_type=normalize_period(raw.get("job_salary_period")),
            employment_type=raw.get("job_employment_type"),
        )

    def _check_rate_limit(self) -> None:
        """Log warning when approaching monthly rate limit."""
        threshold = int(self._monthly_limit * _RATE_LIMIT_WARN)
        if self._request_count >= threshold:
            logger.warning(
                "JSearch rate limit: %d/%d requests used this month",
                self._request_count,
                self._monthly_limit,
            )

    def _raise_api_error(self, resp: httpx.Response) -> None:
        detail = resp.text
        try:
            body = resp.json()
            detail = body.get("message", body.get("error", detail))
        except Exception:
            pass
        raise JSearchAPIError(resp.status_code, detail)

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()
