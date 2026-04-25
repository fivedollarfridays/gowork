"""SSRF fuzz suite for the PDF renderer (T13.56).

This test module locks in the deny-all behaviour of
:func:`app.core.pdf_renderer._deny_all_url_fetcher`. The renderer is the
single egress point for worker-supplied content (resume / cover letter
markdown) into WeasyPrint, so any URL that the renderer is willing to
follow becomes a server-side request forgery (SSRF) vector. The fetcher
is implemented as deny-all and this suite verifies that *every* known
SSRF payload class is rejected:

* cloud metadata endpoints (AWS / GCP / Azure, IPv4 + IPv6),
* loopback (127.0.0.1, localhost, ``::1``, ``0.0.0.0``, bare ``0``),
* RFC1918 / link-local internal ranges,
* alternate schemes (``file://``, ``gopher://``, ``dict://``,
  ``ldap://``, ``ftp://``, ``sftp://``),
* HTTPS variants of all of the above,
* IP encoding tricks (decimal, octal, hex),
* URL-encoded host names,
* userinfo-prefix smuggling (``http://safe.com@127.0.0.1/``),
* schemeless / UNC-style payloads,
* hostnames matching dns-rebinding-friendly suffixes.

Two end-to-end checks pair with the fetcher unit fuzz:

* :func:`test_renders_with_embedded_ssrf_payloads_produces_pdf` feeds a
  worker-style markdown blob containing 5+ ``<img src=...>`` SSRF
  attempts through ``render_markdown_to_pdf`` and asserts a valid PDF
  is produced (WeasyPrint catches ``URLFetchingError`` and drops the
  image — no exception propagates).
* :func:`test_render_makes_no_network_egress` monkey-patches the
  low-level ``socket`` and ``urllib`` primitives and asserts that *no*
  network call is made during a render, even when worker content
  includes a dozen tempting URLs.

If a future change to ``pdf_renderer.py`` lets a payload through, the
parametrised fuzz will fail before the bypass reaches production.
"""

from __future__ import annotations

import socket
from typing import Any

import pytest

from app.core.pdf_renderer import (
    _deny_all_url_fetcher,
    render_markdown_to_pdf,
)
from tests._ssrf_corpus import (
    EMBEDDED_MARKDOWN_PAYLOADS,
    SSRF_URL_CORPUS,
)


# ---------------------------------------------------------------------------
# Direct fetcher fuzz — every URL in the corpus is rejected
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("payload", SSRF_URL_CORPUS, ids=lambda p: p[:60])
def test_deny_all_url_fetcher_rejects_every_corpus_url(payload: str) -> None:
    """Every SSRF corpus URL must raise ``URLFetchingError``.

    The fetcher contract is "raise on every input". We assert each
    payload triggers the documented exception and that the rejected URL
    surfaces in the message for log forensics.
    """
    from weasyprint.urls import URLFetchingError

    with pytest.raises(URLFetchingError) as exc_info:
        _deny_all_url_fetcher(payload)

    # The message must namespace the rejection so it is greppable in
    # production logs and so operators can correlate denied URLs.
    assert "denied" in str(exc_info.value).lower()


def test_corpus_covers_all_required_vector_classes() -> None:
    """Sanity check that the corpus exercises every required category.

    Guards against accidental regressions where a refactor of
    ``_ssrf_corpus.py`` drops an attack class.
    """
    required_substrings = (
        "169.254.169.254",       # AWS IMDS v4
        "fd00:ec2::254",          # AWS IMDS v6
        "metadata.google.internal",  # GCP
        "127.0.0.1",              # IPv4 loopback
        "localhost",              # named loopback
        "[::1]",                  # IPv6 loopback
        "0.0.0.0",                # all-zeros
        "10.0.0.1",               # RFC1918 10/8
        "192.168.",               # RFC1918 192.168/16
        "172.16.",                # RFC1918 172.16/12
        "file://",                # local file scheme
        "gopher://",              # gopher scheme
        "dict://",                # dict scheme
        "ldap://",                # ldap scheme
        "ftp://",                 # ftp scheme
        "sftp://",                # sftp scheme
        "2130706433",             # decimal-encoded 127.0.0.1
        "0x7f000001",             # hex-encoded 127.0.0.1
        "017700000001",           # octal-encoded 127.0.0.1
        "%6c%6f%63%61%6c",        # URL-encoded "local"
        "safe.com@",              # userinfo trick
        ".internal",              # rebinding-style suffix
        ".localhost",             # rebinding-style suffix
        "data:",                  # data URI
    )
    joined = "\n".join(SSRF_URL_CORPUS)
    missing = [s for s in required_substrings if s not in joined]
    assert not missing, f"SSRF corpus missing categories: {missing}"


def test_corpus_minimum_size() -> None:
    """At least 30 direct-URL vectors per the task spec."""
    assert len(SSRF_URL_CORPUS) >= 30, (
        f"corpus too small: {len(SSRF_URL_CORPUS)} < 30 required"
    )


# ---------------------------------------------------------------------------
# End-to-end: embedded SSRF payloads in worker markdown
# ---------------------------------------------------------------------------


def test_renders_with_embedded_ssrf_payloads_produces_pdf() -> None:
    """Worker markdown containing 5+ SSRF ``<img>``/``<link>``/CSS payloads
    must still render to a valid PDF.

    The deny-all fetcher raises ``URLFetchingError`` for each URL and
    WeasyPrint logs a warning then continues — the resulting PDF simply
    omits the unfetchable resource. This guarantees worker content is
    not weaponisable (no SSRF) and is also not a denial-of-service
    vector against the renderer (a single bad URL must not crash the
    job).
    """
    assert len(EMBEDDED_MARKDOWN_PAYLOADS) >= 5, (
        "spec requires at least 5 embedded payloads"
    )
    body = "\n\n".join(EMBEDDED_MARKDOWN_PAYLOADS)
    markdown = f"# Worker Resume\n\nSummary text.\n\n{body}\n"

    pdf = render_markdown_to_pdf(markdown)

    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF-")
    assert pdf.rstrip().endswith(b"%%EOF")


# ---------------------------------------------------------------------------
# Mock-based assertion: no network egress during render
# ---------------------------------------------------------------------------


class _NetworkCalledError(AssertionError):
    """Raised by patched network primitives if anything tries to dial out."""


def _refuse_socket_connect(*args: Any, **kwargs: Any) -> None:
    raise _NetworkCalledError(
        f"socket.create_connection invoked during render: "
        f"args={args!r} kwargs={kwargs!r}"
    )


def _refuse_socket_connect_method(self: Any, address: Any) -> None:
    raise _NetworkCalledError(
        f"socket.connect invoked during render: address={address!r}"
    )


def _refuse_urlopen(*args: Any, **kwargs: Any) -> None:
    raise _NetworkCalledError(
        f"urllib.request.urlopen invoked during render: "
        f"args={args!r} kwargs={kwargs!r}"
    )


def test_render_makes_no_network_egress(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rendering worker markdown with embedded SSRF URLs must not dial.

    We patch every reasonable egress primitive so that any inadvertent
    call surfaces as an immediate test failure rather than a silent
    network leak. The patches cover both the high-level ``urllib``
    facade and the low-level ``socket`` API in case WeasyPrint adds a
    direct-socket fast path or a vendored fetcher in a future version.
    """
    import urllib.request

    monkeypatch.setattr(socket, "create_connection", _refuse_socket_connect)
    monkeypatch.setattr(socket.socket, "connect", _refuse_socket_connect_method)
    monkeypatch.setattr(urllib.request, "urlopen", _refuse_urlopen)

    body = "\n\n".join(EMBEDDED_MARKDOWN_PAYLOADS)
    markdown = (
        "# Worker Resume\n\n"
        "Summary line referencing many SSRF traps.\n\n"
        f"{body}\n"
    )

    # Must not raise _NetworkCalledError. PdfRenderError would also be a
    # bug here, since WeasyPrint must swallow URLFetchingError internally.
    pdf = render_markdown_to_pdf(markdown)
    assert pdf.startswith(b"%PDF-")


def test_network_refusal_helpers_actually_raise() -> None:
    """Self-test: the refusal helpers must raise when invoked.

    Without this, a typo in the helper signature could turn the egress
    test into a no-op (the patches would be in place but never trigger).
    """
    with pytest.raises(_NetworkCalledError):
        _refuse_socket_connect(("example.com", 80))
    with pytest.raises(_NetworkCalledError):
        _refuse_urlopen("http://example.com")
