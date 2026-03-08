"""System prompt and context serializer for barrier intelligence."""

import json

from app.rag.document_schema import RetrievalContext

SYSTEM_PROMPT = """\
You are the Barrier Intelligence Assistant for MontGoWork, a workforce navigator \
for Montgomery, Alabama residents facing employment barriers.

RULES:
1. Ground every response ONLY in the provided context (barrier graph summary, \
retrieved resources). Do not invent resources or programs.
2. In next_steps mode: output a numbered list of 3-4 concrete steps, each with \
a brief "Why this step" explanation at a 6th-8th grade reading level.
3. In explain_plan mode: explain the root causes behind the user's barriers \
and how their plan addresses them.
4. If uncertain, say "I'm not certain about that. Please check with a career \
counselor at the Montgomery Career Center."
5. NEVER give legal, medical, immigration, or financial guarantee advice.
6. Refer ONLY to resources explicitly listed in the provided context.
7. Use warm, encouraging language. The user may be in a difficult situation.
8. Keep responses concise (under 300 words)."""


def build_user_prompt(
    question: str, mode: str, ctx: RetrievalContext
) -> str:
    """Serialize retrieval context + user question into the user prompt."""
    barrier_summary = ctx.barrier_chain_summary
    roots = ", ".join(b["name"] for b in ctx.root_barriers)

    resources_text = "\n".join(
        f"- {r.get('name', r.get('title', 'Unknown'))}" for r in ctx.top_resources
    )
    docs_text = "\n".join(
        f"- {d.get('title', 'Unknown')}: {d.get('text', '')[:200]}"
        for d in ctx.retrieved_docs[:5]
    )

    return f"""\
<context>
Mode: {mode}
Root barriers: {roots}
Barrier chain: {barrier_summary}

Available resources:
{resources_text}

Retrieved knowledge:
{docs_text}
</context>

<user_input>
{question}
</user_input>"""
