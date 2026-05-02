"""Pre-canned demo walkthrough builder.

Returns a single JSON dict containing the entire end-to-end demo for one
persona — judges curl one URL, see the full pipeline serialized.

Synchronous, deterministic.  No DB writes.  No LLM calls.  Uses the
demo persona JSON + a static "narrative" of what each pipeline stage
WOULD produce.  This is a marketing dump, not a live run.
"""

from __future__ import annotations

from app.demo.persona_loader import get_persona
from app.modules.matching.confidence_gate import classify_confidence

_FAKE_TOP_MATCH = {
    "carlos": {
        "title": "Material Handler",
        "company": "Amazon DFW7",
        "location": "Fort Worth, TX 76155",
        "relevance_score": 0.78,
        "fair_chance": True,
        "transit_accessible": True,
        "pay_range": "$18.50/hr",
        "score_breakdown": {
            "skills": 0.65, "title_family": 0.85, "industry": 0.80,
            "years": 0.40, "education": 0.25, "certifications": 0.50,
            "industry_aligned": True,
        },
    },
    "nurse": {
        "title": "ICU Registered Nurse",
        "company": "Texas Health Harris Methodist",
        "location": "Fort Worth, TX 76104",
        "relevance_score": 0.92,
        "transit_accessible": True,
        "pay_range": "$38-$48/hr",
        "score_breakdown": {
            "skills": 0.90, "title_family": 0.95, "industry": 1.00,
            "years": 0.85, "education": 0.80, "certifications": 0.90,
            "industry_aligned": True,
        },
    },
    "forklift": {
        "title": "Forklift Operator - DFW7",
        "company": "Amazon",
        "location": "Fort Worth, TX 76155",
        "relevance_score": 0.86,
        "transit_accessible": True,
        "pay_range": "$19.00/hr",
        "score_breakdown": {
            "skills": 0.80, "title_family": 0.90, "industry": 0.85,
            "years": 0.70, "education": 0.30, "certifications": 0.85,
            "industry_aligned": True,
        },
    },
    "welder": {
        "title": "AWS Certified Welder",
        "company": "Bell Helicopter",
        "location": "Fort Worth, TX 76101",
        "relevance_score": 0.88,
        "pay_range": "$26-$32/hr",
        "score_breakdown": {
            "skills": 0.85, "title_family": 0.90, "industry": 0.85,
            "years": 0.65, "education": 0.30, "certifications": 0.95,
            "industry_aligned": True,
        },
    },
    "csr": {
        "title": "Bilingual Customer Service Representative",
        "company": "Charles Schwab",
        "location": "Fort Worth, TX 76102",
        "relevance_score": 0.74,
        "pay_range": "$20-$24/hr",
        "score_breakdown": {
            "skills": 0.70, "title_family": 0.80, "industry": 0.75,
            "years": 0.50, "education": 0.25, "certifications": 0.0,
            "industry_aligned": True,
        },
    },
}


def _make_match(persona_id: str) -> dict:
    return _FAKE_TOP_MATCH.get(persona_id, _FAKE_TOP_MATCH["carlos"])


def _resource_recommendations(persona: dict) -> list[dict]:
    barriers = persona.get("primary_barriers", [])
    out: list[dict] = []
    if "transportation" in barriers:
        out.append({
            "name": "Trinity Metro Bus Pass Program",
            "why": "Discounted bus pass for FW residents commuting to work.",
            "phone": "817-215-8600",
        })
    if "childcare" in barriers:
        out.append({
            "name": "Child Care Associates",
            "why": "Subsidized childcare for FW working families.",
            "phone": "817-794-9760",
        })
    if "criminal_record" in barriers:
        out.append({
            "name": "Cornerstone Assistance Network — Fair Chance Program",
            "why": "Direct intros to fair-chance employers in Tarrant County.",
            "phone": "817-632-6000",
        })
    if "credit" in barriers:
        out.append({
            "name": "Catholic Charities Fort Worth - Financial Coaching",
            "why": "Free credit repair coaching and budgeting help.",
            "phone": "817-534-0814",
        })
    if "training" in barriers:
        out.append({
            "name": "Tarrant County College - Workforce Training",
            "why": "Short-term training programs aligned with local employers.",
            "phone": "817-515-8223",
        })
    return out


def _haiku_explanation_preview(persona: dict, match: dict) -> str:
    return (
        f"You're a strong fit for {match['title']} at {match['company']}. "
        f"Your strongest signals are title_family ({match['score_breakdown']['title_family']:.2f}) "
        f"and industry alignment.\n\n"
        "Monday morning, visit Workforce Solutions for Tarrant County at "
        "1200 Circle Dr — they have direct intros for this employer."
    )


def _next_steps(persona: dict) -> list[str]:
    return [
        "Visit Workforce Solutions for Tarrant County at 1200 Circle Dr Monday at 9am.",
        "Call Trinity Metro at 817-215-8600 to apply for a bus pass.",
        "Apply to the matched job through the Apply link in your plan.",
        "Schedule a follow-up consult with WSTC for two weeks out.",
    ]


def build_walkthrough(persona_id: str) -> dict:
    """Return the full canned walkthrough payload for one persona."""
    persona = get_persona(persona_id)
    match = _make_match(persona_id)
    confidence = classify_confidence([match])
    return {
        "persona": {
            "id": persona["id"],
            "display_name": persona["display_name"],
            "summary": persona["summary"],
            "primary_barriers": persona["primary_barriers"],
        },
        "top_match": match,
        "confidence": {
            "tier": confidence.tier,
            "top_score": confidence.top_score,
            "message": confidence.message,
            "recommended_action": confidence.recommended_action,
        },
        "resource_recommendations": _resource_recommendations(persona),
        "haiku_explanation_preview": _haiku_explanation_preview(persona, match),
        "next_steps": _next_steps(persona),
        "data_sources": [
            "honestjobs:fw-curated-2026-05",
            "trinity-metro:gtfs-2026-04",
            "twc:fairchance-tarrant-2026-04",
        ],
    }
