"""BrightData integration types."""

import ipaddress
from enum import Enum
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


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


_PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("::ffff:0:0/96"),
]

_BLOCKED_HOSTNAMES = {"localhost"}


def _validate_url(url: str) -> str:
    """Validate a single URL: HTTPS-only, no private IPs, no localhost."""
    parsed = urlparse(url)

    if parsed.scheme != "https":
        raise ValueError(f"Only HTTPS URLs are allowed, got {parsed.scheme!r}")

    hostname = parsed.hostname or ""

    if hostname.lower() in _BLOCKED_HOSTNAMES:
        raise ValueError(
            f"URLs targeting localhost or internal hosts are not allowed"
        )

    try:
        addr = ipaddress.ip_address(hostname)
        for network in _PRIVATE_NETWORKS:
            if addr in network:
                raise ValueError(
                    f"URLs targeting private/reserved IP ranges are not allowed"
                )
    except ValueError as exc:
        if "private" in str(exc).lower() or "reserved" in str(exc).lower():
            raise
        # hostname is not an IP address — that's fine

    return url


class TriggerCrawlRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1)

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, urls: list[str]) -> list[str]:
        """Enforce HTTPS-only and block private/internal targets (SSRF prevention)."""
        return [_validate_url(u) for u in urls]


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
