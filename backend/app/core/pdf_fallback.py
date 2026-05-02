"""Pure-Python PDF fallback (fpdf2) for environments without WeasyPrint.

WeasyPrint depends on the GTK3 native stack (``libgobject``, ``libpango``,
``libcairo``). Production runs on Linux where those ship in the base image,
but Windows-dev and slim CI containers fail to load the libraries and the
default renderer raises ``OSError``. This module provides a no-deps
markdown→PDF fallback so the ``/api/plan/{session_id}/pdf`` endpoint stays
functional everywhere — at the cost of a less ornate layout.

The fallback understands a small CommonMark subset: ATX headings (``#``,
``##``, ``###``), bullet/dash lists, ``**bold**``, ``_italic_``, paragraph
text, and ``---`` horizontal rules. Anything else is emitted as plain text.
"""

from __future__ import annotations

import re
from io import BytesIO

__all__ = ["render_markdown_to_pdf_fallback"]


_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_RE = re.compile(r"(?<!\w)_(.+?)_(?!\w)")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^\)]+)\)")


def render_markdown_to_pdf_fallback(markdown_content: str) -> bytes:
    """Render the markdown content to PDF bytes using fpdf2."""
    from fpdf import FPDF

    pdf = FPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_margins(left=20, top=20, right=20)

    for raw_line in markdown_content.splitlines():
        line = raw_line.rstrip()
        if line.startswith("# "):
            _render_heading(pdf, line[2:].strip(), level=1)
        elif line.startswith("## "):
            _render_heading(pdf, line[3:].strip(), level=2)
        elif line.startswith("### "):
            _render_heading(pdf, line[4:].strip(), level=3)
        elif line.strip() in {"---", "***", "___"}:
            _render_rule(pdf)
        elif line.startswith("- ") or line.startswith("* "):
            _render_bullet(pdf, line[2:].strip(), indent=0)
        elif line.startswith("  - ") or line.startswith("  * "):
            _render_bullet(pdf, line[4:].strip(), indent=6)
        elif not line.strip():
            pdf.ln(3)
        else:
            _render_paragraph(pdf, line.strip())

    out = BytesIO()
    pdf.output(out)
    data = out.getvalue()
    if not data:
        raise RuntimeError("fpdf2 returned empty output")
    return data


# ---------------------------------------------------------------------------
# Block helpers
# ---------------------------------------------------------------------------


def _render_heading(pdf, text: str, level: int) -> None:
    sizes = {1: 22, 2: 15, 3: 12}
    size = sizes.get(level, 11)
    pdf.set_font("Helvetica", style="B", size=size)
    pdf.set_text_color(20, 25, 60)
    if level == 1:
        pdf.ln(2)
    else:
        pdf.ln(4)
    pdf.multi_cell(0, size * 0.45, _strip_inline(text))
    if level == 1:
        # Underline under H1 to mimic the WeasyPrint template.
        x1, y = pdf.l_margin, pdf.get_y() + 1
        pdf.set_draw_color(22, 33, 62)
        pdf.set_line_width(0.4)
        pdf.line(x1, y, pdf.w - pdf.r_margin, y)
        pdf.ln(3)
    else:
        pdf.ln(1)


def _render_paragraph(pdf, text: str) -> None:
    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(30, 30, 35)
    _emit_inline_runs(pdf, text)
    pdf.ln(2)


def _render_bullet(pdf, text: str, indent: int = 0) -> None:
    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(30, 30, 35)
    bullet = "•" if indent == 0 else "◦"
    pdf.set_x(pdf.l_margin + indent)
    pdf.cell(5, 5, _safe(bullet))
    _emit_inline_runs(pdf, text, leading_x=pdf.l_margin + indent + 5)


def _render_rule(pdf) -> None:
    pdf.ln(2)
    pdf.set_draw_color(180, 180, 180)
    pdf.set_line_width(0.2)
    y = pdf.get_y()
    pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
    pdf.ln(3)


# ---------------------------------------------------------------------------
# Inline formatting
# ---------------------------------------------------------------------------


def _strip_inline(text: str) -> str:
    text = _BOLD_RE.sub(r"\1", text)
    text = _ITALIC_RE.sub(r"\1", text)
    text = _LINK_RE.sub(r"\1", text)
    return _safe(text)


def _emit_inline_runs(pdf, text: str, *, leading_x: float | None = None) -> None:
    """Emit a paragraph honouring inline ``**bold**`` runs."""
    runs = _split_bold_runs(text)
    if leading_x is not None:
        pdf.set_x(leading_x)
    line_height = 5
    for run_text, is_bold in runs:
        pdf.set_font("Helvetica", style="B" if is_bold else "", size=11)
        pdf.write(line_height, _safe(_LINK_RE.sub(r"\1", _ITALIC_RE.sub(r"\1", run_text))))
    pdf.ln(line_height)


def _split_bold_runs(text: str) -> list[tuple[str, bool]]:
    """Return ``[(text, is_bold)]`` runs for a paragraph."""
    runs: list[tuple[str, bool]] = []
    last = 0
    for m in _BOLD_RE.finditer(text):
        if m.start() > last:
            runs.append((text[last:m.start()], False))
        runs.append((m.group(1), True))
        last = m.end()
    if last < len(text):
        runs.append((text[last:], False))
    return runs or [(text, False)]


def _safe(text: str) -> str:
    """Replace characters fpdf2's default Helvetica can't render."""
    replacements = {
        "—": "-", "–": "-", "•": "-", "◦": "-",
        "“": '"', "”": '"', "‘": "'", "’": "'",
        "·": "-", "→": "->", "←": "<-",
        "📞": "(phone)", "✓": "[check]", "★": "*",
    }
    out = text
    for src, dst in replacements.items():
        out = out.replace(src, dst)
    # Strip any remaining non-Latin-1 codepoints.
    return out.encode("latin-1", errors="replace").decode("latin-1")
