"""System prompt and context serializer for the Barrier Intelligence Assistant."""

from app.rag.document_schema import RetrievalContext

SYSTEM_PROMPT = """You are the Barrier Intelligence Assistant for MontGoWork.
RULES:
1. Ground every response ONLY in the provided context (barrier graph summary, retrieved resources).
2. next_steps mode: output a numbered list of 3-4 concrete steps, each with a "Why this step"
   explanation at 6th-8th grade reading level.
3. explain_plan mode: explain root causes behind the user's current plan.
4. If uncertain: say "I'm not certain — please check with a career counselor."
5. NEVER give legal, medical, immigration, or financial guarantee advice.
6. Refer only to resources explicitly present in the provided context."""


def _format_resources(resources: list[dict]) -> str:
    if not resources:
        return "No resources retrieved."
    lines = []
    for r in resources[:5]:
        name = r.get("name", "Unknown")
        category = r.get("category", "")
        lines.append(f"- {name} ({category})")
    return "\n".join(lines)


def _format_docs(docs: list) -> str:
    if not docs:
        return "No documents retrieved."
    lines = []
    for doc in docs[:5]:
        title = getattr(doc, "title", "") or doc.get("title", "")
        lines.append(f"- {title}")
    return "\n".join(lines)


def build_user_prompt(
    question: str,
    mode: str,
    ctx: RetrievalContext,
) -> str:
    """Serialize RetrievalContext + user question into Claude user prompt."""
    resources_text = _format_resources(ctx.top_resources)
    docs_text = _format_docs(ctx.retrieved_docs)
    return (
        f"MODE: {mode}\n"
        f"BARRIER CHAIN: {ctx.barrier_chain_summary}\n"
        f"USER ZIP: {ctx.user_zip}\n"
        f"USER SCHEDULE: {ctx.user_schedule or 'flexible'}\n\n"
        f"TOP RESOURCES:\n{resources_text}\n\n"
        f"RETRIEVED KNOWLEDGE:\n{docs_text}\n\n"
        f"<user_input>{question}</user_input>"
    )


def build_context_event(ctx: RetrievalContext) -> dict:
    """Build the SSE 'context' event payload."""
    return {
        "root_barriers": ctx.root_barriers,
        "chain": ctx.barrier_chain_summary,
        "top_resource_count": len(ctx.top_resources),
        "retrieved_doc_count": len(ctx.retrieved_docs),
        "latency_ms": round(ctx.retrieval_latency_ms, 1),
    }
