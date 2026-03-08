"""Tests for polished fallback narrative — empathetic, Montgomery-specific."""


class TestFallbackNarrativePolish:
    def test_fallback_with_barriers_is_empathetic(self):
        """Fallback summary should sound caring, not robotic."""
        from app.ai.client import build_fallback_narrative

        plan_data = {
            "barriers": [
                {"type": "credit", "title": "Credit & Financial Health",
                 "actions": ["Check report"], "resources": [
                     {"name": "GreenPath Financial", "phone": "555-1234"}]},
            ],
            "job_matches": [{"title": "CNA", "company": "Baptist Hospital"}],
            "immediate_next_steps": ["Visit career center"],
        }
        result = build_fallback_narrative(
            barriers=["credit"],
            qualifications="Former CNA at Baptist Hospital",
            plan_data=plan_data,
        )
        # Should NOT sound like "Based on your assessment, you have barriers in:"
        assert "barriers in:" not in result.summary
        # Should sound warm/encouraging
        lower = result.summary.lower()
        assert any(word in lower for word in [
            "you", "your", "step", "start", "monday", "first",
        ])

    def test_fallback_references_montgomery(self):
        """Fallback should mention Montgomery-specific context."""
        from app.ai.client import build_fallback_narrative

        plan_data = {
            "barriers": [
                {"type": "transportation", "title": "Transportation Access",
                 "actions": ["Check M-Transit routes"],
                 "resources": [{"name": "M-Transit", "phone": "334-262-7321"}]},
            ],
            "job_matches": [],
            "immediate_next_steps": ["Contact M-Transit"],
        }
        result = build_fallback_narrative(
            barriers=["transportation"],
            qualifications="Warehouse worker",
            plan_data=plan_data,
        )
        lower = result.summary.lower()
        assert "montgomery" in lower or "alabama" in lower or "career center" in lower

    def test_fallback_mentions_matched_jobs_naturally(self):
        """Fallback weaves job titles in naturally, not as a list."""
        from app.ai.client import build_fallback_narrative

        plan_data = {
            "barriers": [
                {"type": "training", "title": "Training & Certification",
                 "actions": ["Renew CNA"], "resources": []},
            ],
            "job_matches": [
                {"title": "CNA", "company": "Baptist Hospital"},
                {"title": "Medical Assistant", "company": "Jackson Hospital"},
            ],
            "immediate_next_steps": ["Renew CNA license"],
        }
        result = build_fallback_narrative(
            barriers=["training"],
            qualifications="Former CNA",
            plan_data=plan_data,
        )
        # Should mention jobs but not with "Matched job opportunities include:"
        assert "Matched job opportunities include:" not in result.summary
        assert "CNA" in result.summary or "job" in result.summary.lower()

    def test_fallback_mentions_contacts_naturally(self):
        """Fallback should weave contacts in naturally."""
        from app.ai.client import build_fallback_narrative

        plan_data = {
            "barriers": [
                {"type": "credit", "title": "Credit & Financial Health",
                 "actions": ["Check report"], "resources": [
                     {"name": "GreenPath Financial", "phone": "555-1234"}]},
            ],
            "job_matches": [],
            "immediate_next_steps": ["Contact GreenPath Financial"],
        }
        result = build_fallback_narrative(
            barriers=["credit"],
            qualifications="",
            plan_data=plan_data,
        )
        # Should include the contact name naturally
        assert "GreenPath" in result.summary

    def test_fallback_empty_plan_still_encouraging(self):
        """Even with empty data, fallback should be warm and actionable."""
        from app.ai.client import build_fallback_narrative

        plan_data = {"barriers": [], "job_matches": [], "immediate_next_steps": []}
        result = build_fallback_narrative(
            barriers=[],
            qualifications="",
            plan_data=plan_data,
        )
        lower = result.summary.lower()
        # Should still be encouraging and Montgomery-specific
        assert "montgomery" in lower or "career center" in lower or "alabama" in lower
        assert len(result.key_actions) >= 1
        # Default action should be Montgomery-specific
        combined = " ".join(result.key_actions).lower()
        assert "montgomery" in combined or "career center" in combined or "alabama" in combined

    def test_fallback_key_actions_are_specific(self):
        """Key actions should be specific steps, not generic advice."""
        from app.ai.client import build_fallback_narrative

        plan_data = {
            "barriers": [
                {"type": "credit", "title": "Credit & Financial Health",
                 "actions": ["Request free credit report from annualcreditreport.com",
                             "Contact a local career center for credit counseling referral"],
                 "resources": [{"name": "GreenPath Financial", "phone": "555-1234"}]},
            ],
            "job_matches": [{"title": "CNA", "company": "Baptist Hospital"}],
            "immediate_next_steps": ["Contact GreenPath Financial (555-1234)"],
        }
        result = build_fallback_narrative(
            barriers=["credit"],
            qualifications="Former CNA",
            plan_data=plan_data,
        )
        assert len(result.key_actions) >= 1
        assert len(result.key_actions) <= 5

    def test_fallback_jobs_sentence_three_titles(self):
        """Three or more job titles use comma-and format (covers line 115)."""
        from app.ai.client import _fallback_jobs_sentence

        result = _fallback_jobs_sentence(["CNA", "Warehouse", "Driver"])
        assert "CNA" in result
        assert "Warehouse" in result
        assert "Driver" in result
        assert "and" in result

    def test_fallback_no_emojis(self):
        """Fallback narrative must not contain emojis."""
        import re
        from app.ai.client import build_fallback_narrative

        plan_data = {
            "barriers": [
                {"type": "credit", "title": "Credit", "actions": ["Check"],
                 "resources": [{"name": "GreenPath", "phone": "555-1234"}]},
            ],
            "job_matches": [{"title": "CNA", "company": "Baptist"}],
            "immediate_next_steps": ["Visit career center"],
        }
        result = build_fallback_narrative(
            barriers=["credit"],
            qualifications="CNA",
            plan_data=plan_data,
        )
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0\U0001f900-\U0001f9FF"
            "\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]+",
            flags=re.UNICODE,
        )
        assert not emoji_pattern.search(result.summary)
        for action in result.key_actions:
            assert not emoji_pattern.search(action)
