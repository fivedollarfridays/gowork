"""Claude API client for generating plan narratives."""

import json
import logging

from anthropic import AsyncAnthropic

from app.ai.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.ai.types import PlanNarrative
from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def generate_narrative(
    barriers: list[str],
    qualifications: str,
    plan_data: dict,
) -> PlanNarrative:
    """Call Claude API to generate a personalized plan narrative.

    Raises anthropic errors (APITimeoutError, etc.) to the caller.
    """
    settings = get_settings()
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        barriers=", ".join(barriers),
        qualifications=qualifications,
        plan_data=json.dumps(plan_data, default=str),
    )

    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = message.content[0].text
    parsed = json.loads(raw)
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
    """Build a structured narrative without AI when the API is unavailable."""
    actions, contacts, job_titles = _extract_actions_and_contacts(plan_data)

    if barriers:
        summary = (
            f"Based on your assessment, you have barriers in: {', '.join(barriers)}. "
            "Here are your recommended next steps to move forward."
        )
    else:
        summary = "Based on your assessment, here are your recommended next steps."

    if job_titles:
        summary += f" Matched job opportunities include: {', '.join(job_titles[:3])}."
    if contacts:
        summary += f" Key contacts: {'; '.join(contacts[:3])}."

    key_actions = actions[:5] if actions else ["Visit the Montgomery Career Center for assistance"]
    return PlanNarrative(summary=summary, key_actions=key_actions)
