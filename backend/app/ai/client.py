"""LLM client for generating plan narratives."""

import json
import logging

from app.ai.llm_client import get_llm_stream
from app.ai.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.ai.types import PlanNarrative

logger = logging.getLogger(__name__)


async def generate_narrative(
    barriers: list[str],
    qualifications: str,
    plan_data: dict,
) -> PlanNarrative:
    """Call LLM to generate a personalized plan narrative.

    Streams the response, collects it, and parses JSON.
    Falls back to mock provider when no API keys are configured.
    """
    user_prompt = USER_PROMPT_TEMPLATE.format(
        barriers=", ".join(barriers),
        qualifications=qualifications,
        plan_data=json.dumps(plan_data, default=str),
    )

    chunks: list[str] = []
    async for chunk in get_llm_stream(SYSTEM_PROMPT, user_prompt):
        chunks.append(chunk)

    raw = "".join(chunks)
    if not raw.strip():
        raise ValueError("LLM returned empty response")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("LLM returned invalid JSON (length=%d)", len(raw))
        raise ValueError("LLM returned invalid JSON") from exc
    return PlanNarrative(**parsed)


def _extract_actions_and_contacts(plan_data: dict) -> tuple[list[str], list[str], list[str]]:
    """Extract actions, contacts, and job titles from plan data."""
    actions = []
    contacts = []
    for barrier_card in plan_data.get("barriers", []):
        actions.extend(barrier_card.get("actions", []))
        for resource in barrier_card.get("resources", []):
            name = resource.get("name", "")
            phone = resource.get("phone", "")
            if name:
                contacts.append(f"{name} ({phone})" if phone else name)
    for step in plan_data.get("immediate_next_steps", []):
        if step not in actions:
            actions.append(step)
    job_titles = [m["title"] for m in plan_data.get("job_matches", []) if m.get("title")]
    return actions, contacts, job_titles


def build_fallback_narrative(
    barriers: list[str],
    qualifications: str,
    plan_data: dict,
) -> PlanNarrative:
    """Build a warm, Montgomery-specific narrative when the AI API is unavailable."""
    actions, contacts, job_titles = _extract_actions_and_contacts(plan_data)
    summary = _build_fallback_summary(barriers, contacts, job_titles)
    key_actions = _build_fallback_actions(actions)
    return PlanNarrative(summary=summary, key_actions=key_actions)


def _fallback_opening(barriers: list[str]) -> str:
    """Return an empathetic opening sentence based on whether barriers exist."""
    if barriers:
        return (
            "You have already taken a big step by identifying what is standing "
            "in your way. That takes real courage."
        )
    return (
        "You are taking an important first step, and there are people in "
        "Montgomery ready to help you move forward."
    )


def _fallback_next_step(contacts: list[str]) -> str:
    """Return a Monday-morning contact step for the fallback narrative."""
    if contacts:
        return (
            f"Your first step Monday morning is to reach out to {contacts[0]} "
            "-- they work with Montgomery residents every day and know exactly "
            "how to help."
        )
    return (
        "Monday morning, head to the Alabama Career Center on Carter Hill Road. "
        "The staff there help Montgomery residents just like you every single day."
    )


def _fallback_jobs_sentence(job_titles: list[str]) -> str:
    """Return a natural sentence about matched jobs, or empty string."""
    if not job_titles:
        return ""
    if len(job_titles) == 1:
        return f"We also found a {job_titles[0]} position that could be a great fit for you."
    if len(job_titles) > 2:
        joined = ", ".join(job_titles[:2]) + " and " + job_titles[2]
    else:
        joined = " and ".join(job_titles[:2])
    return f"We also found openings for {joined} that could be a great fit."


def _build_fallback_summary(
    barriers: list[str],
    contacts: list[str],
    job_titles: list[str],
) -> str:
    """Compose a warm, Montgomery-specific fallback summary."""
    parts = [
        _fallback_opening(barriers),
        _fallback_next_step(contacts),
    ]
    jobs_sentence = _fallback_jobs_sentence(job_titles)
    if jobs_sentence:
        parts.append(jobs_sentence)
    return " ".join(parts)


def _build_fallback_actions(actions: list[str]) -> list[str]:
    """Return up to 5 key actions, with a Montgomery-specific default."""
    if actions:
        return actions[:5]
    return [
        "Visit the Alabama Career Center on Carter Hill Road in Montgomery "
        "for personalized guidance"
    ]
