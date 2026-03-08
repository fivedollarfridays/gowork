"""RAG document schema for the knowledge corpus."""

from pydantic import BaseModel


class RagDocument(BaseModel):
    """A document in the RAG knowledge corpus."""

    id: str
    doc_type: str  # "resource" | "playbook" | "policy_note"
    title: str
    text: str
    barrier_tags: list[str]
    geography: str | None = None
    schedule_type: str | None = None
    transit_accessible: bool = False
    impact_strength: float = 0.0


class RetrievalContext(BaseModel):
    """Assembled context for barrier intelligence prompt."""

    root_barriers: list[dict]
    barrier_chain_summary: str
    top_resources: list[dict]
    retrieved_docs: list[dict]
    user_zip: str | None = None
    user_schedule: str | None = None
    retrieval_latency_ms: float = 0.0
