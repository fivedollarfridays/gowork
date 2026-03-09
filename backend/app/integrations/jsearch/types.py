"""JSearch integration types."""

from pydantic import BaseModel


class JSearchJobRecord(BaseModel):
    """A single job result from the JSearch API."""

    title: str
    company: str | None = None
    location: str | None = None
    description: str | None = None
    url: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_type: str | None = None  # "hourly" | "annual"
    employment_type: str | None = None


class JSearchResponse(BaseModel):
    """Parsed response from the JSearch API."""

    status: str
    request_id: str
    data: list[JSearchJobRecord]


class JSearchConfigError(Exception):
    """Raised when JSearch API key is not configured."""


class JSearchAPIError(Exception):
    """Raised on non-200 responses from the JSearch API."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"JSearch API error {status_code}: {detail}")
