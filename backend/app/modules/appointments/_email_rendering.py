"""HTML / text body rendering for appointment transactional emails (T12.10a).

Extracted from :mod:`transactional_emails` to keep the public module
under the 300-line architecture ceiling. Owns:

* template constants (subjects / middles / closings per category),
* per-send HTML + text assembly (``render_body``),
* the preference-management URL builder,
* the ``build_manage_url`` wrapper around :func:`app.modules.appointments.tokens.sign`.

Rendering is purely functional — no DB, no network, no side effects.
Every user-controlled string is HTML-escaped exactly once by the
assembly helper so templates stay declarative.
"""

from __future__ import annotations

import html
from dataclasses import dataclass

from app.modules.appointments.tokens import TokenAction, sign as tokens_sign
from app.modules.appointments.types import Appointment


# -------------------- Template constants --------------------


CATEGORY_CONFIRM = "appointment_confirmation"
CATEGORY_24H = "appointment_reminder_24h"
CATEGORY_1H = "appointment_reminder_1h"


@dataclass(frozen=True)
class EmailTemplate:
    """Static per-category rendering inputs."""

    category: str
    subject: str
    middle_text: str  # {when} placeholder
    middle_html: str  # {when} placeholder (already-escaped string inserted)
    closing: str


TEMPLATES: dict[str, EmailTemplate] = {
    CATEGORY_CONFIRM: EmailTemplate(
        category=CATEGORY_CONFIRM,
        subject="Your appointment is confirmed",
        middle_text="Your appointment is confirmed for {when}.",
        middle_html=(
            "Your appointment is confirmed for <strong>{when}</strong>."
        ),
        closing="Looking forward to it.",
    ),
    CATEGORY_24H: EmailTemplate(
        category=CATEGORY_24H,
        subject="Reminder: your appointment is tomorrow",
        middle_text=(
            "Quick reminder — your appointment is at {when} "
            "(about 24 hours from now)."
        ),
        middle_html=(
            "Quick reminder — your appointment is at <strong>{when}</strong> "
            "(about 24 hours from now)."
        ),
        closing="See you tomorrow.",
    ),
    CATEGORY_1H: EmailTemplate(
        category=CATEGORY_1H,
        subject="Starting soon: your appointment is in about an hour",
        middle_text="Your appointment is at {when} (about an hour from now).",
        middle_html=(
            "Your appointment is at <strong>{when}</strong> "
            "(about an hour from now)."
        ),
        closing="Talk soon.",
    ),
}


# -------------------- Manage URL --------------------


def build_manage_url(
    appointment_id: int, action: str, *, app_host: str,
) -> str:
    """Return a signed ``/api/appointments/manage`` URL for an action.

    ``action`` must be a :class:`TokenAction` enum value
    (``cancel`` / ``reschedule`` / ``view``). Token is produced by
    T12.10b ``tokens.sign``.
    """
    token = tokens_sign(appointment_id, TokenAction(action))
    return (
        f"{app_host}/api/appointments/manage"
        f"?token={token}&action={action}"
    )


def preference_url(app_host: str) -> str:
    """Return the "manage reminder preferences" link.

    TODO: ``/settings`` does not yet exist as a real page. Kept as its
    own helper so a future settings route has one place to land.
    """
    return f"{app_host}/settings"


# -------------------- Body assembly --------------------


def render_body(
    appointment: Appointment,
    *,
    first_name: str,
    template: EmailTemplate,
    when: str,
    app_host: str,
) -> tuple[str, str]:
    """Return ``(html_body, text_body)`` for one appointment email.

    All user-controlled fields are HTML-escaped exactly once. Both
    cancel and reschedule manage URLs are injected, plus a
    preference-management link (CAN-SPAM exempt, regulatory best
    practice).
    """
    cancel_url = build_manage_url(
        int(appointment.id), "cancel", app_host=app_host,
    )
    resched_url = build_manage_url(
        int(appointment.id), "reschedule", app_host=app_host,
    )
    pref_url = preference_url(app_host)
    when_e = html.escape(when, quote=True)
    text_body = _render_text(
        appointment, first_name=first_name, template=template,
        when=when, cancel_url=cancel_url, resched_url=resched_url,
        pref_url=pref_url,
    )
    html_body = _render_html(
        appointment, first_name=first_name, template=template,
        when_escaped=when_e, cancel_url=cancel_url, resched_url=resched_url,
        pref_url=pref_url,
    )
    return html_body, text_body


def _render_text(
    appointment: Appointment,
    *,
    first_name: str,
    template: EmailTemplate,
    when: str,
    cancel_url: str,
    resched_url: str,
    pref_url: str,
) -> str:
    """Plain-text body — no escaping, safe for text/plain."""
    loc = appointment.location_name or "TBD"
    return (
        f"Hey {first_name},\n\n"
        f"{template.middle_text.format(when=when)}\n\n"
        f"{appointment.title} at {loc}\n\n"
        f"Cancel: {cancel_url}\n"
        f"Reschedule: {resched_url}\n\n"
        f"{template.closing}\n\n"
        f"Manage your reminder preferences: {pref_url}\n"
        "— MontGoWork\n"
    )


def _render_html(
    appointment: Appointment,
    *,
    first_name: str,
    template: EmailTemplate,
    when_escaped: str,
    cancel_url: str,
    resched_url: str,
    pref_url: str,
) -> str:
    """HTML body — every dynamic field is HTML-escaped."""
    name_e = html.escape(first_name, quote=True)
    title_e = html.escape(appointment.title or "", quote=True)
    loc_e = html.escape(appointment.location_name or "", quote=True)
    cancel_e = html.escape(cancel_url, quote=True)
    resched_e = html.escape(resched_url, quote=True)
    pref_e = html.escape(pref_url, quote=True)
    middle_html = template.middle_html.format(when=when_escaped)
    return (
        "<!doctype html><html><body>"
        f"<p>Hey {name_e},</p>"
        f"<p>{middle_html}</p>"
        f"<p><strong>{title_e}</strong> at {loc_e}</p>"
        f'<p><a href="{cancel_e}">Cancel</a> &nbsp; '
        f'<a href="{resched_e}">Reschedule</a></p>'
        f"<p>{html.escape(template.closing, quote=True)}</p>"
        f'<p><a href="{pref_e}">Manage your reminder preferences</a></p>'
        "<p>— MontGoWork</p>"
        "</body></html>"
    )


__all__ = [
    "CATEGORY_1H",
    "CATEGORY_24H",
    "CATEGORY_CONFIRM",
    "EmailTemplate",
    "TEMPLATES",
    "build_manage_url",
    "preference_url",
    "render_body",
]
