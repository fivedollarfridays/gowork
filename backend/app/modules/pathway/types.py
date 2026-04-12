"""Types for the Employment Pathway Engine.

Models multi-step career trajectories with barrier-aware wage
progression and cliff-safe navigation.
"""

from pydantic import BaseModel, Field, computed_field


class CliffWarning(BaseModel):
    """Warning about a benefits cliff at a specific wage transition."""

    program: str
    cliff_wage: float
    monthly_loss: float
    severity: str  # mild, moderate, severe


class PathwayStep(BaseModel):
    """One stage of a career trajectory.

    Each step represents a target job tier, the barriers that must
    be resolved to reach it, and the expected income at that tier.
    """

    stage: int
    title: str
    target_wage: float
    barriers_to_resolve: list[str] = Field(default_factory=list)
    estimated_weeks: int  # cumulative weeks from pathway start
    jobs_accessible: int  # count of matching jobs at this stage
    cliff_warnings: list[CliffWarning] = Field(default_factory=list)
    net_monthly_income: float | None = None
    unlocked_programs: list[str] = Field(default_factory=list)


class CareerPathway(BaseModel):
    """A complete career trajectory from current state to target wage."""

    pathway_id: str
    name: str
    steps: list[PathwayStep]
    total_weeks: int
    final_wage: float
    final_net_monthly: float
    viability_score: float = Field(ge=0.0, le=1.0)


class PathwayResult(BaseModel):
    """Result containing multiple ranked career pathways."""

    pathways: list[CareerPathway]
    current_wage: float
    current_net_monthly: float
    barriers_active: list[str]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def best_pathway(self) -> CareerPathway | None:
        """Return the pathway with highest viability score."""
        if not self.pathways:
            return None
        return max(self.pathways, key=lambda p: p.viability_score)
