"""Tests for Claude AI prompt templates — persona, tone, format."""


class TestSystemPrompt:
    def test_persona_is_workforce_navigator(self):
        """System prompt establishes the career counselor persona."""
        from app.ai.prompts import SYSTEM_PROMPT

        assert "workforce navigator" in SYSTEM_PROMPT.lower()
        assert "Alabama Career Center" in SYSTEM_PROMPT
        assert "Montgomery" in SYSTEM_PROMPT

    def test_tone_warm_and_action_oriented(self):
        """System prompt instructs warm but practical tone."""
        from app.ai.prompts import SYSTEM_PROMPT

        # Should mention empathetic/warm tone
        assert "warm" in SYSTEM_PROMPT.lower() or "caring" in SYSTEM_PROMPT.lower()
        # Should mention action-oriented approach
        assert "action" in SYSTEM_PROMPT.lower()

    def test_montgomery_context_references(self):
        """System prompt references Montgomery-specific resources."""
        from app.ai.prompts import SYSTEM_PROMPT

        assert "M-Transit" in SYSTEM_PROMPT or "M-transit" in SYSTEM_PROMPT
        # Should reference at least one local landmark/resource
        lower = SYSTEM_PROMPT.lower()
        assert "montgomery" in lower

    def test_style_instructions_present(self):
        """System prompt specifies short paragraphs and direct address."""
        from app.ai.prompts import SYSTEM_PROMPT

        lower = SYSTEM_PROMPT.lower()
        # Should instruct short paragraphs
        assert "short" in lower or "paragraph" in lower or "sentence" in lower
        # Should instruct second person
        assert "you" in lower

    def test_json_format_required(self):
        """System prompt requires JSON response with summary and key_actions."""
        from app.ai.prompts import SYSTEM_PROMPT

        assert "JSON" in SYSTEM_PROMPT or "json" in SYSTEM_PROMPT
        assert "summary" in SYSTEM_PROMPT
        assert "key_actions" in SYSTEM_PROMPT

    def test_no_emojis_in_system_prompt(self):
        """System prompt must not contain emoji characters."""
        from app.ai.prompts import SYSTEM_PROMPT

        import re
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0\U0001f900-\U0001f9FF"
            "\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]+",
            flags=re.UNICODE,
        )
        assert not emoji_pattern.search(SYSTEM_PROMPT), "System prompt must not contain emojis"

    def test_untrusted_input_instruction(self):
        """System prompt warns about untrusted user_input tags."""
        from app.ai.prompts import SYSTEM_PROMPT

        assert "<user_input>" in SYSTEM_PROMPT
        assert "untrusted" in SYSTEM_PROMPT.lower()


class TestUserPromptTemplate:
    def test_includes_barrier_placeholder(self):
        """User prompt template accepts barrier information."""
        from app.ai.prompts import USER_PROMPT_TEMPLATE

        assert "{barriers}" in USER_PROMPT_TEMPLATE

    def test_includes_resource_placeholder(self):
        """User prompt template accepts matched resources."""
        from app.ai.prompts import USER_PROMPT_TEMPLATE

        # Should include plan_data or resources placeholder
        assert "{plan_data}" in USER_PROMPT_TEMPLATE

    def test_includes_qualifications_placeholder(self):
        """User prompt template accepts work history / qualifications."""
        from app.ai.prompts import USER_PROMPT_TEMPLATE

        assert "{qualifications}" in USER_PROMPT_TEMPLATE

    def test_asks_for_monday_morning_narrative(self):
        """User prompt template asks for Monday morning framing."""
        from app.ai.prompts import USER_PROMPT_TEMPLATE

        lower = USER_PROMPT_TEMPLATE.lower()
        assert "monday" in lower

    def test_requests_json_schema(self):
        """User prompt template specifies expected JSON response format."""
        from app.ai.prompts import USER_PROMPT_TEMPLATE

        assert "summary" in USER_PROMPT_TEMPLATE
        assert "key_actions" in USER_PROMPT_TEMPLATE

    def test_template_renders_without_error(self):
        """Template renders successfully with sample data."""
        from app.ai.prompts import USER_PROMPT_TEMPLATE

        rendered = USER_PROMPT_TEMPLATE.format(
            barriers="credit (high severity), transportation (medium severity)",
            qualifications="Former CNA at Baptist Hospital, 3 years experience",
            plan_data='{"barriers": [], "job_matches": []}',
            timeline_context="",
        )
        assert "credit" in rendered
        assert "Former CNA" in rendered
        assert len(rendered) > 100

    def test_barriers_wrapped_in_user_input_tags(self):
        """Barriers field is wrapped in <user_input> XML tags."""
        from app.ai.prompts import USER_PROMPT_TEMPLATE

        rendered = USER_PROMPT_TEMPLATE.format(
            barriers="credit, transportation",
            qualifications="test",
            plan_data="{}",
            timeline_context="",
        )
        assert "<user_input>credit, transportation</user_input>" in rendered

    def test_qualifications_wrapped_in_user_input_tags(self):
        """Qualifications field is wrapped in <user_input> XML tags."""
        from app.ai.prompts import USER_PROMPT_TEMPLATE

        rendered = USER_PROMPT_TEMPLATE.format(
            barriers="credit",
            qualifications="Former CNA, 3 years",
            plan_data="{}",
            timeline_context="",
        )
        assert "<user_input>Former CNA, 3 years</user_input>" in rendered

    def test_plan_data_wrapped_in_user_input_tags(self):
        """plan_data field is wrapped in <user_input> tags (MED-4 prompt injection defense)."""
        from app.ai.prompts import USER_PROMPT_TEMPLATE

        rendered = USER_PROMPT_TEMPLATE.format(
            barriers="credit",
            qualifications="test",
            plan_data='{"barriers": [], "job_matches": []}',
            timeline_context="",
        )
        assert '<user_input>{"barriers": [], "job_matches": []}</user_input>' in rendered

    def test_no_emojis_in_user_prompt(self):
        """User prompt template must not contain emoji characters."""
        from app.ai.prompts import USER_PROMPT_TEMPLATE

        import re
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0\U0001f900-\U0001f9FF"
            "\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]+",
            flags=re.UNICODE,
        )
        assert not emoji_pattern.search(USER_PROMPT_TEMPLATE), "User prompt must not contain emojis"
