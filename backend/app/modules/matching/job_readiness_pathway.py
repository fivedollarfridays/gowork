"""Career pathway generation for Job Readiness Score.

City-aware: uses resource_router for career center names.
"""

from app.modules.matching.job_readiness_types import (
    ReadinessFactor,
    ReadinessPathwayStep,
)
from app.modules.matching.resource_router import get_career_center
from app.modules.matching.types import UserProfile

_WEAK_THRESHOLD = 60


def _get_step_templates() -> dict[str, tuple[str, str, int]]:
    """Return step templates using the active city's career center."""
    cc = get_career_center()
    return {
        "Skills Match": (
            "Build job-relevant skills through training programs",
            cc.name,
            30,
        ),
        "Industry Alignment": (
            "Explore target industries and identify transferable skills",
            cc.name,
            14,
        ),
        "Barrier Resolution": (
            "Address barriers with community resources in your plan",
            "See barrier cards above",
            60,
        ),
        "Work Experience": (
            "Create or update your resume highlighting relevant experience",
            f"{cc.name} resume workshop",
            7,
        ),
        "Credit Readiness": (
            "Follow your credit repair pathway to improve eligibility",
            "See credit assessment results",
            90,
        ),
    }


def build_pathway(
    profile: UserProfile,
    factors: list[ReadinessFactor],
) -> list[ReadinessPathwayStep]:
    """Generate actionable steps for factors below threshold."""
    weak = sorted(
        (f for f in factors if f.score < _WEAK_THRESHOLD),
        key=lambda f: f.score,
    )
    if not weak:
        return []

    templates = _get_step_templates()
    steps: list[ReadinessPathwayStep] = []
    for i, factor in enumerate(weak, start=1):
        template = templates.get(factor.name)
        if template:
            action, resource, days = template
            steps.append(ReadinessPathwayStep(
                step_number=i, action=action,
                resource=resource, timeline_days=days,
            ))

    return steps
