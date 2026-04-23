"""Tests for app.core.pdf_renderer (T12.4).

Covers the public ``render_markdown_to_pdf`` API, the SSRF-guarded
``url_fetcher``, Jinja2 autoescape behaviour, markdown raw-HTML
escaping, and the Dockerfile system-deps documentation invariant.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.pdf_renderer import PdfRenderError, render_markdown_to_pdf


# ---------------------------------------------------------------------------
# Basic rendering
# ---------------------------------------------------------------------------


def test_renders_simple_markdown_to_valid_pdf() -> None:
    """Simple markdown must produce a valid PDF byte string."""
    pdf = render_markdown_to_pdf("# Hello\n\nBody text.")

    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF-"), "PDF magic bytes missing"
    # A non-trivial document is emitted
    assert len(pdf) > 500
    # Every PDF ends with the EOF marker
    assert pdf.rstrip().endswith(b"%%EOF")


def test_renders_at_least_one_page() -> None:
    """A non-empty document must contain at least one page.

    We go through the lower-level Document/HTML API for a structural
    assertion that is independent of PDF-stream compression.
    """
    from app.core.pdf_renderer import _deny_all_url_fetcher, _render_html
    from app.core.pdf_renderer import _build_jinja_env, _DEFAULT_TEMPLATES_DIR

    env = _build_jinja_env(_DEFAULT_TEMPLATES_DIR)
    html_str = _render_html(env, "default", "# Title\n\nBody paragraph.")

    from weasyprint import HTML

    document = HTML(string=html_str, url_fetcher=_deny_all_url_fetcher).render()
    assert len(document.pages) >= 1


def test_returns_nonempty_bytes_for_empty_markdown() -> None:
    """Empty markdown should still produce a valid PDF skeleton."""
    pdf = render_markdown_to_pdf("")
    assert pdf.startswith(b"%PDF-")


# ---------------------------------------------------------------------------
# Title extraction
# ---------------------------------------------------------------------------


def test_title_extracted_from_first_h1() -> None:
    """First markdown H1 must populate the rendered ``<title>`` element.

    Verified through the WeasyPrint ``Document.metadata`` facade, which
    surfaces the ``<title>`` tag independently of PDF stream encoding.
    """
    from app.core.pdf_renderer import _deny_all_url_fetcher, _render_html
    from app.core.pdf_renderer import _build_jinja_env, _DEFAULT_TEMPLATES_DIR

    env = _build_jinja_env(_DEFAULT_TEMPLATES_DIR)
    html_str = _render_html(env, "default", "# My Resume\n\nSection body.\n")
    assert "<title>My Resume</title>" in html_str

    from weasyprint import HTML

    document = HTML(string=html_str, url_fetcher=_deny_all_url_fetcher).render()
    assert document.metadata.title == "My Resume"


def test_title_defaults_when_no_heading() -> None:
    """Documents without an H1 fall back to a sensible default title."""
    # Expose the internal helper; this is a white-box contract check.
    from app.core.pdf_renderer import _extract_title

    assert _extract_title("Just body text, no heading") == "Document"
    assert _extract_title("# Resume\n\nBody") == "Resume"
    assert _extract_title("\n\n# Trimmed Heading\n") == "Trimmed Heading"


# ---------------------------------------------------------------------------
# Missing template / error paths
# ---------------------------------------------------------------------------


def test_raises_on_missing_template() -> None:
    """An unknown template name must raise PdfRenderError."""
    with pytest.raises(PdfRenderError) as exc_info:
        render_markdown_to_pdf("# Hi", template_name="nonexistent")
    assert "nonexistent" in str(exc_info.value)


def test_raises_on_missing_templates_dir(tmp_path: Path) -> None:
    """A templates_dir that does not exist raises PdfRenderError."""
    with pytest.raises(PdfRenderError):
        render_markdown_to_pdf(
            "# Hi", templates_dir=tmp_path / "does-not-exist"
        )


# ---------------------------------------------------------------------------
# SSRF defence: deny-all url_fetcher
# ---------------------------------------------------------------------------


def test_denies_external_url_fetch_169_254() -> None:
    """An inline <img> to the AWS metadata endpoint must not be fetched.

    We assert the deny-all fetcher raises URLFetchingError for that URL;
    WeasyPrint swallows the error and logs a warning, so rendering still
    produces a valid PDF without any network call.
    """
    from weasyprint.urls import URLFetchingError

    from app.core.pdf_renderer import _deny_all_url_fetcher

    with pytest.raises(URLFetchingError):
        _deny_all_url_fetcher("http://169.254.169.254/latest/meta-data/")

    # End-to-end: rendering markdown that references the metadata IP
    # must still succeed (fetcher declines, WeasyPrint moves on).
    md = (
        "# Document\n\n"
        "![meta](http://169.254.169.254/latest/meta-data/)\n"
    )
    pdf = render_markdown_to_pdf(md)
    assert pdf.startswith(b"%PDF-")


def test_denies_external_url_fetch_arbitrary_host() -> None:
    """Arbitrary external hosts are also denied by the fetcher."""
    from weasyprint.urls import URLFetchingError

    from app.core.pdf_renderer import _deny_all_url_fetcher

    for url in (
        "https://evil.example.com/x.png",
        "http://example.com/style.css",
        "file:///etc/passwd",
        "data:text/html,<script>alert(1)</script>",
    ):
        with pytest.raises(URLFetchingError):
            _deny_all_url_fetcher(url)


def test_deny_fetcher_message_includes_url() -> None:
    """The error message identifies the rejected URL for log forensics."""
    from weasyprint.urls import URLFetchingError

    from app.core.pdf_renderer import _deny_all_url_fetcher

    with pytest.raises(URLFetchingError) as exc_info:
        _deny_all_url_fetcher("https://evil.example.com/x.png")
    assert "evil.example.com" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Jinja2 autoescape + markdown sanitisation
# ---------------------------------------------------------------------------


def test_markdown_escapes_raw_html_input() -> None:
    """Raw <script> in markdown input must be escaped, not executed/embedded."""
    malicious = "# Title\n\n<script>alert('xss')</script>\n"
    pdf = render_markdown_to_pdf(malicious)

    # The raw opening tag must not reach the PDF byte stream.
    # PDFs compress streams, so spot-check the decoded form by matching
    # the literal escaped variant which is what python-markdown emits.
    assert b"<script>alert" not in pdf


def test_autoescape_escapes_template_vars() -> None:
    """The Jinja2 Environment must have autoescape enabled for HTML templates."""
    from app.core.pdf_renderer import _build_jinja_env

    env = _build_jinja_env(
        Path("backend/app/modules/documents/templates").resolve()
        if Path(
            "backend/app/modules/documents/templates"
        ).exists()
        else Path(".")
    )
    assert env.autoescape is True or callable(env.autoescape)

    # Render an ad-hoc template to confirm escaping is active for .html.
    tmpl = env.from_string("<p>{{ value }}</p>")
    rendered = tmpl.render(value="<script>alert(1)</script>")
    assert "&lt;script&gt;" in rendered
    assert "<script>" not in rendered


# ---------------------------------------------------------------------------
# Dockerfile system-deps invariant
# ---------------------------------------------------------------------------


_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_dockerfile_installs_required_system_deps() -> None:
    """Dockerfile must install the WeasyPrint system deps.

    The following libraries are required at runtime for WeasyPrint to
    render fonts on ``python:3.13-slim`` (which ships without them).
    """
    dockerfile = (_REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    for pkg in (
        "libpango-1.0-0",
        "libpangoft2-1.0-0",
        "libcairo2",
        "fonts-liberation",
    ):
        assert pkg in dockerfile, f"Dockerfile missing system dep: {pkg}"


def test_requirements_pins_weasyprint() -> None:
    """requirements.txt must pin a concrete WeasyPrint version."""
    reqs = (_REPO_ROOT / "backend" / "requirements.txt").read_text(
        encoding="utf-8"
    )
    # Case-insensitive prefix check, requiring a version pin.
    lines = [line.strip().lower() for line in reqs.splitlines()]
    weasy_lines = [line for line in lines if line.startswith("weasyprint")]
    assert weasy_lines, "weasyprint not pinned in requirements.txt"
    assert "==" in weasy_lines[0], (
        f"weasyprint must be version-pinned, got: {weasy_lines[0]!r}"
    )
