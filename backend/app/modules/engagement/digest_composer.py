"""Daily digest composer for a worker session (T12.20, S12a).

Composes a structured email digest with up to four sections (yesterday
wins, today's plan, this-week outlook, stall alert). Empty sections are
omitted. See ``digest_data`` for DB-facing collection and
``digest_sections`` / ``digest_rendering`` for section + line renderers.

Worker first-name resolution
----------------------------
Read from the ``sessions.profile`` JSON TEXT column in priority order:

    1. ``profile.first_name`` — authoritative if present.
    2. ``profile.name`` — first whitespace-delimited token used.
    3. ``"friend"`` — neutral fallback.

The ``sessions`` schema (migration m001) has no dedicated first-name
column, so the JSON blob is the only source. Logic lives in
``digest_data.resolve_first_name`` and is documented there too.

HTML escaping
-------------
Every worker-supplied dynamic value (name, appointment title, company,
role, notes, barrier ids) flows through ``html.escape`` at the template
boundary — just before interpolation. Plaintext reuses raw values.
"""

from __future__ import annotations

import html
from datetime import date, datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from app.modules.engagement.digest_data import (
    collect_this_week,
    collect_today,
    collect_yesterday,
    resolve_first_name,
)
from app.modules.engagement.digest_sections import (
    Section,
    render_stall_alerts_section,
    render_this_week_section,
    render_today_section,
    render_yesterday_section,
)
from app.modules.engagement.stall_detector import compute_stall_for_session

_EMPTY_PLACEHOLDER = "Nothing new today — keep going."


class DigestResult(BaseModel):
    """Composed digest payload: subject + HTML + plaintext + section counts."""

    subject: str
    html: str
    text: str
    section_counts: dict[str, int]


def _subject_for(for_date: date) -> str:
    label = for_date.strftime("%A, %b %d")
    return f"[MontGoWork] Your daily digest — {label}"


def _build_sections(
    *,
    session_id: str,
    for_date: date,
    db_path: str | Path,
    now: datetime,
    city: str,
) -> list[Section]:
    """Assemble the 0-4 non-empty sections in fixed order."""
    y_bundle, cleared = collect_yesterday(session_id, for_date, db_path)
    today_items, yesterday_missed = collect_today(
        session_id, for_date, db_path, now, city,
    )
    week_items = collect_this_week(session_id, for_date, db_path, now, city)
    stall = compute_stall_for_session(session_id, db_path=db_path, now=now)

    sections: list[Section] = []
    candidates = [
        render_yesterday_section(y_bundle, cleared),
        render_today_section(today_items, yesterday_missed, for_date),
        render_this_week_section(week_items),
        render_stall_alerts_section(stall),
    ]
    for section in candidates:
        if section is not None:
            sections.append(section)
    return sections


def _section_counts(sections: list[Section]) -> dict[str, int]:
    """Return observability counts keyed by section id (always all 4 keys)."""
    counts = {"yesterday": 0, "today": 0, "week": 0, "stall": 0}
    for section in sections:
        counts[section.section_id] = section.item_count
    return counts


def _render_html(first_name: str, sections: list[Section]) -> str:
    """Assemble the HTML document from escaped greeting + section bodies."""
    greeting = html.escape(first_name)
    parts = [f"<p>Hi {greeting},</p>"]
    if not sections:
        parts.append(f"<p>{_EMPTY_PLACEHOLDER}</p>")
    else:
        for section in sections:
            parts.append(
                f"<h2>{html.escape(section.title)}</h2>\n{section.html_body}"
            )
    return "\n".join(parts)


def _render_text(first_name: str, sections: list[Section]) -> str:
    """Assemble the plaintext document (mirrors HTML structure)."""
    parts = [f"Hi {first_name},", ""]
    if not sections:
        parts.append(_EMPTY_PLACEHOLDER)
    else:
        for section in sections:
            parts.append(section.title)
            parts.append(section.text_body)
            parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def compose_digest(
    session_id: str,
    for_date: date,
    *,
    db_path: str | Path,
    city: str | None = None,
    now: datetime | None = None,
) -> DigestResult:
    """Build today's digest as {subject, html, text, section_counts}.

    Sections are omitted when empty. ``city`` defaults to
    ``settings.city``. ``now`` is injectable for test determinism;
    default is the UTC wall clock.

    See module docstring for first-name resolution + HTML escaping rules.
    """
    now = now or datetime.now(timezone.utc)
    if city is None:
        from app.core.config import get_settings
        city = get_settings().city
    first_name = resolve_first_name(db_path, session_id)
    sections = _build_sections(
        session_id=session_id,
        for_date=for_date,
        db_path=db_path,
        now=now,
        city=city,
    )
    return DigestResult(
        subject=_subject_for(for_date),
        html=_render_html(first_name, sections),
        text=_render_text(first_name, sections),
        section_counts=_section_counts(sections),
    )


__all__ = ["DigestResult", "compose_digest"]
