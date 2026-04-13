"""Tests verifying app.ai.prompts is deprecated and raises warning."""

import warnings


class TestPromptsDeprecated:
    """Verify the legacy prompts module is deprecated."""

    def test_importing_prompts_raises_deprecation_warning(self):
        """Importing app.ai.prompts should emit DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            import importlib
            import app.ai.prompts
            importlib.reload(app.ai.prompts)
            deprecation_warnings = [
                x for x in w if issubclass(x.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) >= 1
            assert "deprecated" in str(deprecation_warnings[0].message).lower()
