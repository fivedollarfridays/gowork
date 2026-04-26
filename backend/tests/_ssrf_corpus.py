"""SSRF payload corpus for the PDF renderer fuzz suite (T13.56).

Kept in a separate module from ``test_pdf_ssrf_fuzz.py`` so the test
file stays comfortably under the architecture line-count limit, and so
the corpus can be reused by future tests (e.g. URL allow-list checks
on other egress points).

Each payload exercises a distinct SSRF class. Add to this list when a
new attack surface is discovered. **Never** remove entries — historic
vectors have a habit of resurfacing through library upgrades.
"""

from __future__ import annotations

__all__ = ["EMBEDDED_MARKDOWN_PAYLOADS", "SSRF_URL_CORPUS"]


# ---------------------------------------------------------------------------
# Direct URL corpus — fed one-by-one to ``_deny_all_url_fetcher``.
# Each must independently raise ``URLFetchingError``.
# ---------------------------------------------------------------------------


_CLOUD_METADATA = (
    # AWS instance metadata service (IPv4 and the lesser-known IPv6).
    "http://169.254.169.254/latest/meta-data/",
    "https://169.254.169.254/latest/meta-data/iam/security-credentials/",
    "http://[fd00:ec2::254]/latest/meta-data/",
    # GCP metadata.
    "http://metadata.google.internal/computeMetadata/v1/",
    "https://metadata.google.internal/computeMetadata/v1/instance/",
    # Azure IMDS uses the same 169.254 base; include the canonical path.
    "http://169.254.169.254/metadata/instance?api-version=2021-02-01",
)

_LOOPBACK = (
    "http://127.0.0.1/",
    "https://127.0.0.1/admin",
    "http://localhost/",
    "https://localhost:8080/internal",
    "http://[::1]/",
    "https://[::1]:9200/",
    "http://0.0.0.0/",
    "http://0/",  # bare zero — resolves to 0.0.0.0 on most stacks
)

_RFC1918 = (
    "http://10.0.0.1/",
    "http://10.255.255.255/admin",
    "http://192.168.1.1/router",
    "http://192.168.0.254/",
    "http://172.16.0.1/",
    "http://172.31.255.254/",
    "https://10.0.0.1/internal",
)

_ALT_SCHEMES = (
    "file:///etc/passwd",
    "file://localhost/etc/hosts",
    "file:///proc/self/environ",
    "gopher://attacker.com:11211/_stats",
    "gopher://127.0.0.1:6379/_INFO",
    "dict://internal:11211/stats",
    "ldap://internal-ldap/dc=example,dc=com",
    "ldaps://internal-ldap/",
    "ftp://internal-ftp/",
    "sftp://internal-ftp/",
    "data:text/html,<script>alert(1)</script>",
)

_IP_ENCODING = (
    # Decimal-encoded 127.0.0.1 = 2130706433.
    "http://2130706433/",
    # Octal-encoded 127.0.0.1.
    "http://017700000001/",
    # Hex-encoded 127.0.0.1.
    "http://0x7f000001/",
    # Mixed dotted-hex.
    "http://0x7f.0x0.0x0.0x1/",
    # Decimal-encoded 169.254.169.254 = 2852039166.
    "http://2852039166/latest/meta-data/",
)

_OBFUSCATION = (
    # URL-encoded "localhost".
    "http://%6c%6f%63%61%6c%68%6f%73%74/",
    # URL-encoded "127.0.0.1".
    "http://%31%32%37%2e%30%2e%30%2e%31/",
    # Userinfo-prefix smuggling — naive parsers see safe.com, real host is the IP.
    "http://safe.com@127.0.0.1/",
    "https://trusted.example.com@169.254.169.254/latest/meta-data/",
    # Schemeless / protocol-relative.
    "//attacker.com/",
    "//169.254.169.254/latest/meta-data/",
    # Windows UNC-style (some libraries dereference these).
    "\\\\attacker.com\\share",
)

_DNS_REBIND_SUFFIXES = (
    # Hostnames that *look* friendly but the deny-all must reject regardless.
    "http://anything.localhost/",
    "http://service.internal/secret",
    "http://node-1.cluster.local/",
    "http://intranet.corp/",
    "http://api.internal:8080/health",
    # Documented dns-rebinding service domains.
    "http://7f000001.nip.io/",
    "http://attacker.localtest.me/",
)


SSRF_URL_CORPUS: tuple[str, ...] = (
    *_CLOUD_METADATA,
    *_LOOPBACK,
    *_RFC1918,
    *_ALT_SCHEMES,
    *_IP_ENCODING,
    *_OBFUSCATION,
    *_DNS_REBIND_SUFFIXES,
)


# ---------------------------------------------------------------------------
# Embedded-in-markdown payloads — fed as a single document through
# ``render_markdown_to_pdf`` to exercise the WeasyPrint integration.
# Each payload must produce a finished PDF (deny-all + WeasyPrint warn-and-skip).
# ---------------------------------------------------------------------------


EMBEDDED_MARKDOWN_PAYLOADS: tuple[str, ...] = (
    # Markdown image syntax pointing at AWS IMDS.
    "![pwn](http://169.254.169.254/latest/meta-data/)",
    # Raw HTML <img> in markdown — markdown library escapes it but worth
    # exercising the path in case a future content extension turns it on.
    '<img src="http://127.0.0.1/admin" alt="x">',
    # Markdown image to internal RFC1918 host.
    "![](http://10.0.0.1/internal)",
    # Markdown link to a file:// URI.
    "[secrets](file:///etc/passwd)",
    # Markdown image to a gopher attack URL.
    "![](gopher://attacker.com:11211/_stats)",
    # Markdown image with userinfo smuggling.
    "![icon](http://safe.com@169.254.169.254/latest/meta-data/)",
    # CSS @import via raw HTML <style> — likewise escaped by markdown,
    # included for defence-in-depth coverage.
    '<style>@import url("http://internal/leak.css");</style>',
)
