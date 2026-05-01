"""Tests verifying barrier_intel modules don't cache at import time."""

import ast
from pathlib import Path


class TestBarrierIntelNoCaching:
    """Verify barrier_intel modules don't freeze values at import time."""

    def test_prompts_no_module_level_system_prompt(self):
        """barrier_intel/prompts.py must not assign SYSTEM_PROMPT at module level."""
        source = Path("app/barrier_intel/prompts.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "SYSTEM_PROMPT":
                        # Check if it's a function call (cached result)
                        if isinstance(node.value, ast.Call):
                            assert False, (
                                "SYSTEM_PROMPT must not be cached at module level. "
                                "Callers should use get_barrier_intel_system_prompt() directly."
                            )

    def test_guardrails_no_module_level_disclaimer(self):
        """barrier_intel/guardrails.py must not assign HALLUCINATION_DISCLAIMER at module level."""
        source = Path("app/barrier_intel/guardrails.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "HALLUCINATION_DISCLAIMER":
                        if isinstance(node.value, ast.Call):
                            assert False, (
                                "HALLUCINATION_DISCLAIMER must not be cached at module level. "
                                "Callers should use _get_hallucination_disclaimer() directly."
                            )
