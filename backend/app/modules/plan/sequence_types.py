"""Types for barrier sequencing engine."""

from pydantic import BaseModel, Field


class SequenceStep(BaseModel):
    """A single step in a barrier resolution sequence."""

    order: int
    barrier_id: str
    barrier_name: str
    category: str
    playbook: str
    unlocks: list[str] = Field(default_factory=list)
    estimated_weeks: int = 4


class BarrierSequence(BaseModel):
    """Topologically sorted barrier resolution plan."""

    steps: list[SequenceStep]
    total_barriers: int
    has_cycles: bool = False
    estimated_total_weeks: int = 0
