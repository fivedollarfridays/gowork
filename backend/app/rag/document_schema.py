"""RagDocument — canonical document model for the RAG knowledge corpus."""

from pydantic import BaseModel, field_validator


class RagDocument(BaseModel):
    id: str
    doc_type: str  # "resource" | "playbook" | "policy_note"
    title: str
    text: str
    barrier_tags: list[str]
    geography: str | None = None
    schedule_type: str | None = None  # "day" | "evening" | "flexible" | None
    transit_accessible: bool = False
    impact_strength: float = 0.0

    @field_validator("barrier_tags")
    @classmethod
    def tags_must_be_non_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("barrier_tags must not be empty")
        return v
