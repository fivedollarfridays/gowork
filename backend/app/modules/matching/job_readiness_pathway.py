"""Career pathway generation for Job Readiness Score."""

from app.modules.matching.job_readiness_types import (
    ReadinessFactor,
    ReadinessPathwayStep,
)
from app.modules.matching.types import UserProfile

_WEAK_THRESHOLD = 60

# Map factor names to pathway step templates: (action, resource, days)
_STEP_TEMPLATES: dict[str, tuple[str, str, int]] = {
    "Skills Match": (
        "Build job-relevant skills through training programs",
        "Montgomery Career Center",
        30,
    ),
    "Industry Alignment": (
        "Explore target industries and identify transferable skills",
        "AIDT (Alabama Industrial Development Training)",
        14,
    ),
    "Barrier Resolution": (
        "Address barriers with community resources in your plan",
        "See barrier cards above",
        60,
    ),
    "Work Experience": (
        "Create or update your resume highlighting relevant experience",
        "Montgomery Career Center resume workshop",
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

    steps: list[ReadinessPathwayStep] = []
    for i, factor in enumerate(weak, start=1):
        template = _STEP_TEMPLATES.get(factor.name)
        if template:
            action, resource, days = template
            steps.append(ReadinessPathwayStep(
                step_number=i, action=action,
                resource=resource, timeline_days=days,
            ))

    return steps
