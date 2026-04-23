"""Small HTML/plaintext rendering primitives for the digest composer.

Hosts the ported ops:lib helpers (dedupe, stale detection, carryover
tier formatting) plus line-level formatters for appointments and stall
CTAs. Keeps ``digest_composer`` + ``digest_sections`` under the arch
limits by pushing leaf-level string work here.
"""

from __future__ import annotations

import html
from datetime import timezone

from app.modules.appointments.types import Appointment
from app.modules.common.temporal_types import StallLevel

PREP_HINT = "30 minutes before: review directions and bring ID."

# Direct port of ``ops:lib/daily_plan_dedupe.SOURCE_PRIORITY``. Appointments
# don't have an arbitrary source tag, so we score by appointment type: live
# human-scheduled (court/interview) outranks placeholders.
_TYPE_PRIORITY: dict[str, int] = {
    "court_hearing": 1,
    "job_interview": 1,
    "benefits_recert": 2,
    "medical": 2,
    "dmv": 3,
    "career_center": 3,
    "childcare_intake": 3,
    "other": 4,
}


def _type_rank(appt: Appointment) -> int:
    return _TYPE_PRIORITY.get(appt.type.value, 99)


def dedupe_appointments_by_slot(
    appts: list[Appointment],
) -> list[Appointment]:
    """Port of ``dedupe_by_time_slot`` — collapse same-slot appointments.

    Groups by ``(starts_at, ends_at)``; winner is the highest-priority
    type, tie-broken by longer title. Returns appointments sorted by
    start time.
    """
    groups: dict[tuple, list[Appointment]] = {}
    for a in appts:
        groups.setdefault((a.starts_at, a.ends_at), []).append(a)
    winners: list[Appointment] = []
    for group in groups.values():
        if len(group) == 1:
            winners.append(group[0])
            continue
        group.sort(key=lambda x: (_type_rank(x), -len(x.title or "")))
        winners.append(group[0])
    return sorted(winners, key=lambda x: x.starts_at or x.starts_at)


def schedule_title_stale(
    title: str, past_blocks: list[dict], threshold: int = 2,
) -> bool:
    """Port of ``_schedule_title_stale`` — True when a title keeps rolling.

    Original ops:lib version tracked 7+ emissions with no ``done=True``;
    we reuse the same shape (list of block dicts carrying ``title`` +
    ``done``) but lower the threshold since the digest window is a
    single day's worth of missed appointments, not a week of schedule
    emissions. ``threshold`` stays parameterized for future tuning.
    """
    emissions = 0
    done_seen = False
    for block in past_blocks:
        if block.get("title") != title:
            continue
        emissions += 1
        if block.get("done"):
            done_seen = True
    return emissions >= threshold and not done_seen


def format_appointment_html(
    appt: Appointment, prep_hint: str | None,
) -> str:
    """Escape + format a single appointment line for HTML."""
    time_str = _local_hhmm(appt)
    title = html.escape(appt.title)
    location = html.escape(appt.location_name or "")
    parts = [f"{time_str}: {title}"]
    if location:
        parts.append(f"at {location}")
    if prep_hint:
        parts.append(html.escape(prep_hint))
    return " — ".join(parts)


def format_appointment_text(
    appt: Appointment, prep_hint: str | None,
) -> str:
    """Plaintext variant — same structure, no HTML escaping."""
    time_str = _local_hhmm(appt)
    parts = [f"- {time_str}: {appt.title}"]
    if appt.location_name:
        parts.append(f"at {appt.location_name}")
    if prep_hint:
        parts.append(prep_hint)
    return " — ".join(parts)


def _local_hhmm(appt: Appointment) -> str:
    if appt.starts_at is None:
        return "TBD"
    local = appt.starts_at.astimezone(timezone.utc)
    return local.strftime("%H:%M")


def format_carryover_html(carry: list[tuple[str, int]]) -> str:
    """Port of ``render_carryover`` — tier-formatted HTML for carried items."""
    by_tier: dict[int, list[str]] = {}
    for title, tier in carry:
        by_tier.setdefault(tier, []).append(title)
    lines = ["<p>Carried over from yesterday:</p>"]
    for tier in sorted(by_tier.keys(), reverse=True):
        titles = sorted(by_tier[tier])
        noun = "item" if len(titles) == 1 else "items"
        lines.append(
            f"<p>Rolled {tier}x ({len(titles)} {noun}):</p>"
        )
        lines.append("<ul>")
        for title in titles:
            lines.append(f"  <li>{html.escape(title)}</li>")
        lines.append("</ul>")
    return "\n".join(lines)


def format_carryover_text(carry: list[tuple[str, int]]) -> str:
    """Plaintext tier-formatted carryover."""
    by_tier: dict[int, list[str]] = {}
    for title, tier in carry:
        by_tier.setdefault(tier, []).append(title)
    lines = ["Carried over from yesterday:"]
    for tier in sorted(by_tier.keys(), reverse=True):
        titles = sorted(by_tier[tier])
        noun = "item" if len(titles) == 1 else "items"
        lines.append(f"Rolled {tier}x ({len(titles)} {noun}):")
        for title in titles:
            lines.append(f"  - {title}")
    return "\n".join(lines)


def stall_cta_lines(
    level: StallLevel, days: int,
) -> tuple[str, str]:
    """Return (html_body, text_body) for a stall CTA at the given level."""
    if level is StallLevel.HARD:
        msg = (
            f"It's been {days} days since your last step forward. "
            "We're here to help — want to talk with a navigator?"
        )
    elif level is StallLevel.MEDIUM:
        msg = (
            f"It's been about {days} days. "
            "We can help you map out a next step if you're stuck."
        )
    else:  # SOFT
        msg = (
            f"Quick check-in — about {days} days since your last update. "
            "Everything still on track?"
        )
    return f"<p>{html.escape(msg)}</p>", msg


__all__ = [
    "PREP_HINT",
    "dedupe_appointments_by_slot",
    "format_appointment_html",
    "format_appointment_text",
    "format_carryover_html",
    "format_carryover_text",
    "schedule_title_stale",
    "stall_cta_lines",
]
