"""Branch helpers for cover_letter_builder (T12.16).

Extracted to keep the main module under the function-count limit.
Two responsibilities:

* Decide which barriers to address ("frame") on a given letter.
* Build the per-branch template context and LLM prompt body.

The fair-chance branch frames cleared barriers — most importantly
``criminal_record`` — using *employment-gap* language rather than
loaded labels. The non-fair-chance branch suppresses any record
disclosure, so the framing list is empty.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "barriers_to_frame",
    "build_template_context",
    "build_llm_prompt",
]

# Cleared-barrier keys that imply an employment gap worth narrating.
_GAP_BARRIERS: frozenset[str] = frozenset({
    "criminal_record", "incarceration", "treatment", "homelessness",
})


def barriers_to_frame(
    profile: dict[str, Any], *, is_fair_chance: bool,
) -> list[str]:
    """Return the cleared-barrier keys to address in this letter.

    Non-fair-chance employers always get an empty list — the cover
    letter omits the record entirely. Fair-chance employers see the
    intersection of ``profile.cleared_barriers`` with the gap-implying
    set above; order is preserved from the profile.
    """
    if not is_fair_chance:
        return []
    cleared = profile.get("cleared_barriers") or []
    if not isinstance(cleared, list):
        return []
    return [b for b in cleared if isinstance(b, str) and b in _GAP_BARRIERS]


def build_template_context(
    profile: dict[str, Any],
    job_match_ref: dict[str, Any],
    *,
    is_fair_chance: bool,
    barriers_framed: list[str],
    date_today: str,
) -> dict[str, Any]:
    """Compose the Jinja context for ``cover_letter_base.md.j2``.

    The ``opening`` and ``body`` are deterministic strings built from
    sanitised profile fields; ``fair_chance_framing`` is non-empty only
    when the fair-chance branch fires AND there are barriers to frame.
    """
    name = str(profile.get("name") or "")
    summary = str(profile.get("summary") or "")
    employer = str(job_match_ref.get("employer") or "the team")
    title = str(job_match_ref.get("title") or "this role")
    opening = (
        f"I am writing to express my interest in the {title} position "
        f"at {employer}."
    )
    body = summary or (
        "I bring reliable attendance, a steady work ethic, and a "
        "willingness to learn on the job."
    )
    return {
        "date_today": date_today,
        "hiring_manager": str(job_match_ref.get("hiring_manager") or ""),
        "name": name,
        "opening": opening,
        "body": body,
        "fair_chance_framing": _gap_framing(barriers_framed) if is_fair_chance else "",
    }


def build_llm_prompt(
    profile: dict[str, Any],
    job_match_ref: dict[str, Any],
    *,
    is_fair_chance: bool,
    barriers_framed: list[str],
) -> str:
    """Compose the LLM prompt — sanitised profile + branch directives.

    Kept as a thin string builder so the module under test can stub
    ``_call_llm`` directly.
    """
    bits = [
        "Write a worker cover letter in markdown.",
        "Name: " + str(profile.get("name") or ""),
        "Employer: " + str(job_match_ref.get("employer") or ""),
        "Role: " + str(job_match_ref.get("title") or ""),
    ]
    if is_fair_chance and barriers_framed:
        framing = _gap_framing(barriers_framed)
        bits.append(
            "Address the employment gap directly with this framing: "
            + framing
        )
    else:
        bits.append("Do not mention the worker's criminal record.")
    return "\n\n".join(bits)


# -------------------- Internal --------------------


def _gap_framing(barriers_framed: list[str]) -> str:
    """One-sentence employment-gap narrative for the fair-chance branch.

    Names the cleared barrier(s) using neutral language. The
    :mod:`app.modules.documents.voice` post-processor strips any
    loaded labels that may slip through.
    """
    if not barriers_framed:
        return ""
    if "criminal_record" in barriers_framed:
        return (
            "I want to be upfront about a gap in my employment "
            "history. I have completed the steps required to move "
            "forward and am focused on a steady transition into "
            "this role."
        )
    return (
        "I had a period of time away from the workforce while "
        "resolving a personal situation, and I am now ready to "
        "transition back into steady work."
    )
