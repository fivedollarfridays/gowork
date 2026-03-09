"""Tests for URL validation on TriggerCrawlRequest (HIGH-2 / MED-1)."""

import pytest
from pydantic import ValidationError

from app.integrations.brightdata.types import TriggerCrawlRequest


class TestSchemeValidation:
    """Only HTTPS URLs should be accepted."""

    def test_https_url_accepted(self):
        req = TriggerCrawlRequest(urls=["https://indeed.com/jobs?l=Montgomery+AL"])
        assert req.urls == ["https://indeed.com/jobs?l=Montgomery+AL"]

    def test_http_url_rejected(self):
        with pytest.raises(ValidationError, match="(?i)https"):
            TriggerCrawlRequest(urls=["http://indeed.com/jobs"])

    def test_file_url_rejected(self):
        with pytest.raises(ValidationError, match="(?i)https"):
            TriggerCrawlRequest(urls=["file:///etc/passwd"])

    def test_ftp_url_rejected(self):
        with pytest.raises(ValidationError, match="(?i)https"):
            TriggerCrawlRequest(urls=["ftp://files.example.com/data"])

    def test_gopher_url_rejected(self):
        with pytest.raises(ValidationError, match="(?i)https"):
            TriggerCrawlRequest(urls=["gopher://gopher.example.com"])

    def test_mixed_valid_and_invalid_rejected(self):
        """One bad URL in the list should reject the entire request."""
        with pytest.raises(ValidationError, match="(?i)https"):
            TriggerCrawlRequest(urls=[
                "https://indeed.com/jobs",
                "http://evil.com/ssrf",
            ])


class TestPrivateIpRejection:
    """URLs pointing to private/reserved IP ranges must be blocked (SSRF)."""

    def test_loopback_127_rejected(self):
        with pytest.raises(ValidationError, match="(?i)private|internal|reserved"):
            TriggerCrawlRequest(urls=["https://127.0.0.1/admin"])

    def test_loopback_127_x_rejected(self):
        with pytest.raises(ValidationError, match="(?i)private|internal|reserved"):
            TriggerCrawlRequest(urls=["https://127.0.0.99/"])

    def test_10_network_rejected(self):
        with pytest.raises(ValidationError, match="(?i)private|internal|reserved"):
            TriggerCrawlRequest(urls=["https://10.0.0.1/internal"])

    def test_172_16_network_rejected(self):
        with pytest.raises(ValidationError, match="(?i)private|internal|reserved"):
            TriggerCrawlRequest(urls=["https://172.16.0.1/"])

    def test_172_31_network_rejected(self):
        with pytest.raises(ValidationError, match="(?i)private|internal|reserved"):
            TriggerCrawlRequest(urls=["https://172.31.255.255/"])

    def test_192_168_network_rejected(self):
        with pytest.raises(ValidationError, match="(?i)private|internal|reserved"):
            TriggerCrawlRequest(urls=["https://192.168.1.1/"])

    def test_link_local_169_254_rejected(self):
        with pytest.raises(ValidationError, match="(?i)private|internal|reserved"):
            TriggerCrawlRequest(urls=["https://169.254.169.254/latest/meta-data/"])

    def test_aws_metadata_endpoint_rejected(self):
        """Classic cloud SSRF vector: AWS instance metadata service."""
        with pytest.raises(ValidationError, match="(?i)private|internal|reserved"):
            TriggerCrawlRequest(urls=["https://169.254.169.254/latest/api/token"])


class TestIPv6Rejection:
    """IPv6 private/loopback addresses must also be blocked."""

    def test_ipv6_loopback_rejected(self):
        with pytest.raises(ValidationError, match="(?i)private|internal|reserved"):
            TriggerCrawlRequest(urls=["https://[::1]/admin"])

    def test_ipv6_link_local_rejected(self):
        with pytest.raises(ValidationError, match="(?i)private|internal|reserved"):
            TriggerCrawlRequest(urls=["https://[fe80::1]/"])

    def test_ipv4_mapped_ipv6_rejected(self):
        with pytest.raises(ValidationError, match="(?i)private|internal|reserved"):
            TriggerCrawlRequest(urls=["https://[::ffff:127.0.0.1]/"])

    def test_ipv6_unique_local_rejected(self):
        with pytest.raises(ValidationError, match="(?i)private|internal|reserved"):
            TriggerCrawlRequest(urls=["https://[fd00::1]/"])


class TestLocalhostRejection:
    """URLs with localhost or internal hostnames must be blocked."""

    def test_localhost_rejected(self):
        with pytest.raises(ValidationError, match="(?i)private|internal|localhost"):
            TriggerCrawlRequest(urls=["https://localhost/admin"])

    def test_localhost_with_port_rejected(self):
        with pytest.raises(ValidationError, match="(?i)private|internal|localhost"):
            TriggerCrawlRequest(urls=["https://localhost:8080/"])

    def test_0_0_0_0_rejected(self):
        with pytest.raises(ValidationError, match="(?i)private|internal|reserved"):
            TriggerCrawlRequest(urls=["https://0.0.0.0/"])


class TestValidUrls:
    """Valid HTTPS URLs to public hosts should pass."""

    def test_multiple_valid_urls(self):
        req = TriggerCrawlRequest(urls=[
            "https://indeed.com/jobs?l=Montgomery+AL",
            "https://www.ziprecruiter.com/jobs/search?q=&l=Montgomery%2C+AL",
        ])
        assert len(req.urls) == 2

    def test_url_with_path_and_query(self):
        req = TriggerCrawlRequest(urls=[
            "https://www.linkedin.com/jobs/search/?keywords=&location=Montgomery",
        ])
        assert len(req.urls) == 1

    def test_public_ip_accepted(self):
        """A public IP address (not in private ranges) should be fine."""
        req = TriggerCrawlRequest(urls=["https://8.8.8.8/"])
        assert req.urls == ["https://8.8.8.8/"]
