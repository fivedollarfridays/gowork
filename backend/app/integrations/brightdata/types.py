"""BrightData integration types."""

from enum import Enum

from pydantic import BaseModel, Field


class CrawlStatus(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    READY = "ready"
    FAILED = "failed"


class CrawlRequest(BaseModel):
    urls: list[str]
    dataset_id: str
    output_fields: str = "markdown|ld_json|html2text"


class CrawlProgress(BaseModel):
    snapshot_id: str
    status: CrawlStatus
    progress_pct: float | None = None


class CrawlResult(BaseModel):
    snapshot_id: str
    jobs: list[dict]


class BrightDataConfigError(Exception):
    """Raised when BrightData API key or dataset ID is not configured."""


class BrightDataAPIError(Exception):
    """Raised on non-2xx responses from the BrightData API."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"BrightData API error {status_code}: {detail}")


class BrightDataTimeoutError(Exception):
    """Raised when polling exceeds max retries."""


class TriggerCrawlRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1)


class TriggerCrawlResponse(BaseModel):
    snapshot_id: str
    status: CrawlStatus
    message: str


class CrawlStatusResponse(BaseModel):
    snapshot_id: str
    status: CrawlStatus
    progress_pct: float | None = None
    jobs_found: int | None = None
    message: str


class BrightDataJobRecord(BaseModel):
    title: str
    company: str | None = None
    location: str | None = None
    description: str | None = None
    url: str | None = None
