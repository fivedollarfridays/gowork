"""Tests for AI narrative enhancement with timeline phases (T31.2)."""

import json

import pytest

from app.ai.types import PlanNarrative

# --- Shared test fixtures (module-level constants) ---

_ACTION_CAREER = {
    "category": "career_center", "title": "Visit Alabama Career Center",
    "detail": "Bring ID and resume", "priority": 1, "source_module": "always",
    "resource_name": "Alabama Career Center", "resource_phone": "334-286-1746",
}
_ACTION_JOB = {
    "category": "job_application", "title": "Apply for CNA position",
    "detail": None, "priority": 2, "source_module": "jobs",
    "resource_name": "Baptist Health", "resource_phone": None,
}
_ACTION_CREDIT = {
    "category": "credit_repair", "title": "Request free credit report",
    "detail": "Visit annualcreditreport.com", "priority": 1,
    "source_module": "credit", "resource_name": "GreenPath Financial",
    "resource_phone": "800-550-1961",
}

_EMPTY_PLAN_DATA = {"barriers": [], "job_matches": [], "immediate_next_steps": []}


def _make_phase(phase_id: str, label: str, start: int, end: int, actions: list) -> dict:
    """Build a single timeline phase dict."""
    return {
        "phase_id": phase_id, "label": label,
        "start_day": start, "end_day": end, "actions": actions,
    }


def _make_action(cat: str, title: str, **kw) -> dict:
    """Build a single action dict with defaults."""
    return {
        "category": cat, "title": title, "detail": kw.get("detail"),
        "priority": kw.get("priority", 1), "source_module": kw.get("source", "test"),
        "resource_name": kw.get("name"), "resource_phone": kw.get("phone"),
    }


def _five_phase_plan() -> dict:
    """Return a sample action plan with all 5 timeline phases."""
    return {
        "assessment_date": "2026-03-09",
        "total_actions": 5,
        "phases": [
            _make_phase("week_1_2", "Week 1-2: Quick Wins", 1, 14,
                        [_make_action("career_center", "Visit Alabama Career Center",
                                      detail="Bring ID", name="Alabama Career Center",
                                      phone="334-286-1746")]),
            _make_phase("month_1", "Month 1: Foundation", 15, 30,
                        [_make_action("job_application", "Apply for CNA",
                                      name="Baptist Health", source="jobs")]),
            _make_phase("month_2_3", "Month 2-3: Building Momentum", 31, 90,
                        [_make_action("credit_repair", "Follow up on disputes",
                                      detail="Check online", phone="800-550-1961")]),
            _make_phase("month_3_6", "Month 3-6: Stability", 91, 180,
                        [_make_action("training", "Complete ITA-funded training",
                                      source="wioa")]),
            _make_phase("month_6_12", "Month 6-12: Growth", 181, 365,
                        [_make_action("benefits_enrollment", "Review cliff transition",
                                      detail="Re-assess eligibility", source="cliff")]),
        ],
    }


class TestPlanNarrativeModel:
    """PlanNarrative model should accept phase_summaries."""

    def test_phase_summaries_accepted(self):
        """PlanNarrative should accept a phase_summaries list of strings."""
        narrative = PlanNarrative(
            summary="Monday morning, head to the Career Center.",
            key_actions=["Visit Career Center"],
            phase_summaries=["Week 1-2: Visit Career Center", "Month 1: Apply for jobs"],
        )
        assert narrative.phase_summaries == [
            "Week 1-2: Visit Career Center",
            "Month 1: Apply for jobs",
        ]

    def test_phase_summaries_defaults_empty(self):
        """Backwards compat: phase_summaries defaults to empty list."""
        narrative = PlanNarrative(
            summary="Your first step is to visit the Career Center.",
            key_actions=["Visit Career Center"],
        )
        assert narrative.phase_summaries == []


class TestFormatTimelineContext:
    """format_timeline_context() formats ActionPlan phases for the LLM prompt."""

    def test_formats_phases_with_actions(self):
        """Should produce readable text with phase labels and action details."""
        from app.ai.client import format_timeline_context

        action_plan = {
            "assessment_date": "2026-03-09", "total_actions": 3,
            "phases": [
                _make_phase("week_1_2", "Week 1-2: Quick Wins", 1, 14,
                            [_ACTION_CAREER, _ACTION_JOB]),
                _make_phase("month_1", "Month 1: Foundation", 15, 30,
                            [_ACTION_CREDIT]),
            ],
        }
        result = format_timeline_context(action_plan)
        for expected in ["Week 1-2: Quick Wins", "Month 1: Foundation",
                         "Visit Alabama Career Center", "334-286-1746",
                         "Apply for CNA position", "Request free credit report"]:
            assert expected in result

    def test_returns_empty_for_none(self):
        """Should return empty string when no action plan provided."""
        from app.ai.client import format_timeline_context

        assert format_timeline_context(None) == ""

    def test_returns_empty_for_no_phases(self):
        """Should return empty string when action plan has no phases."""
        from app.ai.client import format_timeline_context

        result = format_timeline_context({
            "assessment_date": "2026-03-09", "total_actions": 0, "phases": [],
        })
        assert result == ""


class TestFallbackWithTimeline:
    """build_fallback_narrative() should produce phase_summaries from action_plan."""

    def test_with_action_plan_produces_phase_summaries(self):
        """Fallback with action_plan should include non-empty phase_summaries."""
        from app.ai.client import build_fallback_narrative

        result = build_fallback_narrative(
            barriers=[], qualifications="", plan_data=_EMPTY_PLAN_DATA,
            action_plan=_five_phase_plan(),
        )
        assert len(result.phase_summaries) > 0

    def test_without_action_plan_empty_phase_summaries(self):
        """Fallback without action_plan should have empty phase_summaries."""
        from app.ai.client import build_fallback_narrative

        result = build_fallback_narrative(
            barriers=[], qualifications="", plan_data=_EMPTY_PLAN_DATA,
        )
        assert result.phase_summaries == []

    def test_phase_summaries_match_5_phases(self):
        """With 5-phase plan, fallback should produce 5 phase summaries."""
        from app.ai.client import build_fallback_narrative

        result = build_fallback_narrative(
            barriers=[], qualifications="", plan_data=_EMPTY_PLAN_DATA,
            action_plan=_five_phase_plan(),
        )
        assert len(result.phase_summaries) == 5
        assert "Week 1-2" in result.phase_summaries[0]
        assert "Month 1" in result.phase_summaries[1]


class TestPromptTemplateTimeline:
    """USER_PROMPT_TEMPLATE should include a timeline_context placeholder."""

    def test_prompt_has_timeline_placeholder(self):
        """Prompt template should include {timeline_context} placeholder."""
        from app.ai.prompts import USER_PROMPT_TEMPLATE

        assert "{timeline_context}" in USER_PROMPT_TEMPLATE


def _one_phase_plan() -> dict:
    """Return a single-phase action plan for generate_narrative tests."""
    return {
        "assessment_date": "2026-03-09", "total_actions": 1,
        "phases": [
            _make_phase("week_1_2", "Week 1-2: Quick Wins", 1, 14,
                        [_make_action("career_center", "Visit Alabama Career Center",
                                      detail="Bring ID", name="Alabama Career Center",
                                      phone="334-286-1746")]),
        ],
    }


class TestGenerateNarrativeWithTimeline:
    """generate_narrative() should accept action_plan and include timeline in prompt."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_passes_action_plan_to_prompt(monkeypatch):
        """generate_narrative with action_plan should include timeline in prompt."""
        from app.ai import client as client_module

        captured: list[str] = []

        async def capturing_stream(_sys: str, user_prompt: str):
            captured.append(user_prompt)
            yield json.dumps({"summary": "Monday morning.", "key_actions": ["Step 1"]})

        monkeypatch.setattr(client_module, "get_llm_stream", capturing_stream)

        result = await client_module.generate_narrative(
            barriers=["credit"], qualifications="CNA",
            plan_data={"barriers": [], "job_matches": []},
            action_plan=_one_phase_plan(),
        )
        assert len(captured) == 1
        assert "Week 1-2: Quick Wins" in captured[0]
        assert "Visit Alabama Career Center" in captured[0]
        assert isinstance(result, PlanNarrative)
