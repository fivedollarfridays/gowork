"""Section renderers for the digest composer (T12.20, S12a).

Split from ``digest_composer`` to keep both modules under the 300-line
architecture ceiling. Each ``render_*_section`` function returns either
a :class:`Section` (non-empty) or ``None`` (section omitted).

Helpers factored further into ``digest_rendering`` for HTML/text
formatting primitives so this file stays under the 12-function limit.
"""

from __future__ import annotations

import html
from datetime import date, datetime, timezone

from pydantic import BaseModel

from app.modules.appointments.types import Appointment
from app.modules.common.temporal_types import StallLevel
from app.modules.engagement.digest_rendering import (
    PREP_HINT,
    dedupe_appointments_by_slot,
    format_appointment_html,
    format_appointment_text,
    format_carryover_html,
    format_carryover_text,
    schedule_title_stale,
    stall_cta_lines,
)
from app.modules.engagement.stall_detector import StalledSession
from app.modules.plan.evidence_collector import EvidenceBundle


class Section(BaseModel):
    """Rendered digest section ready for composition into HTML/text."""

    section_id: str  # "yesterday" | "today" | "week" | "stall"
    title: str
    html_body: str
    text_body: str
    item_count: int


# -------------------- Yesterday --------------------


def render_yesterday_section(
    bundle: EvidenceBundle, cleared_barriers: list[str],
) -> Section | None:
    """Render yesterday's wins — attended appts, filed apps, cleared barriers."""
    attended = bundle.appointments_attended
    filed = bundle.applications_filed
    progressed = bundle.applications_progressed
    apps = list(filed) + [a for a in progressed if a not in filed]

    item_count = len(attended) + len(apps) + len(cleared_barriers)
    if item_count == 0:
        return None

    html_lines: list[str] = []
    text_lines: list[str] = []
    if attended:
        _emit_yesterday_appointments(attended, html_lines, text_lines)
    if apps:
        _emit_yesterday_applications(apps, html_lines, text_lines)
    if cleared_barriers:
        _emit_yesterday_barriers(cleared_barriers, html_lines, text_lines)

    return Section(
        section_id="yesterday",
        title="Yesterday",
        html_body="\n".join(html_lines),
        text_body="\n".join(text_lines),
        item_count=item_count,
    )


def _emit_yesterday_appointments(
    attended: list[Appointment],
    html_lines: list[str],
    text_lines: list[str],
) -> None:
    noun = "appointment" if len(attended) == 1 else "appointments"
    html_lines.append(f"<p>{len(attended)} {noun} attended:</p>")
    html_lines.append("<ul>")
    text_lines.append(f"{len(attended)} {noun} attended:")
    for appt in attended:
        html_lines.append(f"  <li>{html.escape(appt.title)}</li>")
        text_lines.append(f"- {appt.title}")
    html_lines.append("</ul>")


def _emit_yesterday_applications(
    apps: list, html_lines: list[str], text_lines: list[str],
) -> None:
    noun = "application" if len(apps) == 1 else "applications"
    html_lines.append(f"<p>{len(apps)} {noun} filed or progressed:</p>")
    html_lines.append("<ul>")
    text_lines.append(f"{len(apps)} {noun} filed or progressed:")
    for app in apps:
        company = app.company or "Unknown"
        role = app.role or "role"
        label = f"{company} — {role}"
        html_lines.append(f"  <li>{html.escape(label)}</li>")
        text_lines.append(f"- {label}")
    html_lines.append("</ul>")


def _emit_yesterday_barriers(
    cleared_barriers: list[str],
    html_lines: list[str],
    text_lines: list[str],
) -> None:
    count = len(cleared_barriers)
    noun = "barrier" if count == 1 else "barriers"
    html_lines.append(f"<p>{count} {noun} cleared:</p>")
    html_lines.append("<ul>")
    text_lines.append(f"{count} {noun} cleared:")
    for name in cleared_barriers:
        html_lines.append(f"  <li>{html.escape(name)}</li>")
        text_lines.append(f"- {name}")
    html_lines.append("</ul>")


# -------------------- Today --------------------


def render_today_section(
    today_items: list[Appointment],
    yesterday_missed: list[Appointment],
    for_date: date,
) -> Section | None:
    """Render today's upcoming appointments with prep hints + carryover."""
    deduped = dedupe_appointments_by_slot(today_items)
    carry_titles = _compute_carryover(yesterday_missed)
    if not deduped and not carry_titles:
        return None

    html_lines: list[str] = []
    text_lines: list[str] = []
    _emit_today_appointments(deduped, html_lines, text_lines)
    if carry_titles:
        html_lines.append(format_carryover_html(carry_titles))
        text_lines.append(format_carryover_text(carry_titles))

    return Section(
        section_id="today",
        title="Today",
        html_body="\n".join(html_lines),
        text_body="\n".join(text_lines),
        item_count=len(deduped) + len(carry_titles),
    )


def _compute_carryover(
    yesterday_missed: list[Appointment],
) -> list[tuple[str, int]]:
    """Tier-mark yesterday's undone items via the ported stale helper."""
    out: list[tuple[str, int]] = []
    for appt in yesterday_missed:
        stale = schedule_title_stale(
            appt.title, [{"title": appt.title, "done": False}],
        )
        out.append((appt.title, 2 if stale else 1))
    return out


def _emit_today_appointments(
    deduped: list[Appointment],
    html_lines: list[str],
    text_lines: list[str],
) -> None:
    if not deduped:
        return
    html_lines.append("<p>Today's appointments:</p>")
    html_lines.append("<ul>")
    text_lines.append("Today's appointments:")
    for appt in deduped:
        html_lines.append(
            f"  <li>{format_appointment_html(appt, PREP_HINT)}</li>"
        )
        text_lines.append(format_appointment_text(appt, PREP_HINT))
    html_lines.append("</ul>")


# -------------------- This week --------------------


def render_this_week_section(
    week_items: list[Appointment],
) -> Section | None:
    """Render upcoming-in-7-days appointments.

    S12a scope note: the fair-chance jobs feed and benefits-recert
    reminders have no upstream data source yet, so those sub-sections
    are skipped here. TODO S12b: add them once feeds land.
    """
    # TODO(S12b): include newly listed fair-chance jobs (no feed yet).
    # TODO(S12b): include upcoming benefits-recert dates (no tracking).
    if not week_items:
        return None
    html_lines = ["<p>This week:</p>", "<ul>"]
    text_lines = ["This week:"]
    for appt in sorted(week_items, key=_appt_sort_key):
        day_label = _day_label(appt.starts_at)
        html_lines.append(
            f"  <li>{html.escape(day_label)}: "
            f"{format_appointment_html(appt, None)}</li>"
        )
        text_lines.append(f"- {day_label}: {format_appointment_text(appt, None)}")
    html_lines.append("</ul>")
    return Section(
        section_id="week",
        title="This week",
        html_body="\n".join(html_lines),
        text_body="\n".join(text_lines),
        item_count=len(week_items),
    )


def _day_label(dt: datetime | None, city: str | None = None) -> str:
    if dt is None:
        return "TBD"
    if city:
        from app.modules.common.temporal_types import TIMEZONE_BY_CITY
        from zoneinfo import ZoneInfo
        tz_name = TIMEZONE_BY_CITY.get(city)
        if tz_name:
            local = dt.astimezone(ZoneInfo(tz_name))
            return f"{local.strftime('%a')} {local.month}/{local.day}"
    local = dt.astimezone(timezone.utc)
    return f"{local.strftime('%a')} {local.month}/{local.day}"


def _appt_sort_key(appt: Appointment) -> datetime:
    return appt.starts_at or datetime.max.replace(tzinfo=timezone.utc)


# -------------------- Stall alerts --------------------


def render_stall_alerts_section(
    stall: StalledSession,
) -> Section | None:
    """Render tiered stall CTA — HARD routes to advisor, SOFT/MEDIUM soften."""
    if stall.stall_level is StallLevel.NONE:
        return None
    html_body, text_body = stall_cta_lines(stall.stall_level, stall.days_stalled)
    return Section(
        section_id="stall",
        title="Check-in",
        html_body=html_body,
        text_body=text_body,
        item_count=1,
    )


__all__ = [
    "Section",
    "render_stall_alerts_section",
    "render_this_week_section",
    "render_today_section",
    "render_yesterday_section",
]
