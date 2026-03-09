from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """Claude API interprets a resident's situation."""
    extracted_qualifications: list[str]
    certification_status: list[dict]  # {type, status, renewal_body, timeline}
    barrier_interpretation: str  # Human-readable summary


class PlanNarrative(BaseModel):
    """Claude API generates the Monday Morning summary paragraph."""
    summary: str  # "Monday morning, walk to the Route 7 bus stop..."
    key_actions: list[str]  # Top 3-5 prioritized actions
    phase_summaries: list[str] = Field(default_factory=list)
