"""Tests for multi-provider LLM config fields."""

import pytest

from app.core.config import Settings, get_settings


class TestLlmConfigDefaults:
    """Verify new LLM config fields have correct defaults."""

    def setup_method(self):
        get_settings.cache_clear()

    def test_llm_provider_defaults_to_anthropic(self):
        s = Settings(environment="development")
        assert s.llm_provider == "anthropic"

    def test_openai_api_key_defaults_empty(self):
        s = Settings(environment="development")
        assert s.openai_api_key == ""

    def test_openai_model_has_default(self):
        s = Settings(environment="development")
        assert s.openai_model == "gpt-4o"

    def test_gemini_api_key_defaults_empty(self):
        s = Settings(environment="development")
        assert s.gemini_api_key == ""

    def test_gemini_model_has_default(self):
        s = Settings(environment="development")
        assert s.gemini_model == "gemini-2.0-flash"


class TestLlmConfigFromEnv:
    """Verify LLM fields can be set via environment variables."""

    def setup_method(self):
        get_settings.cache_clear()

    def test_llm_provider_from_env(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        s = Settings(environment="development")
        assert s.llm_provider == "openai"

    def test_openai_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai")
        s = Settings(environment="development")
        assert s.openai_api_key == "sk-test-openai"

    def test_gemini_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "gemini-key-123")
        s = Settings(environment="development")
        assert s.gemini_api_key == "gemini-key-123"

    def test_mock_provider_accepted(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        s = Settings(environment="development")
        assert s.llm_provider == "mock"


class TestLlmConfigAuditLog:
    """Verify audit log path config field."""

    def setup_method(self):
        get_settings.cache_clear()

    def test_audit_log_path_defaults_empty(self):
        s = Settings(environment="development")
        assert s.audit_log_path == ""

    def test_audit_log_path_from_env(self, monkeypatch):
        monkeypatch.setenv("AUDIT_LOG_PATH", "/var/log/montgowork/audit.jsonl")
        s = Settings(environment="development")
        assert s.audit_log_path == "/var/log/montgowork/audit.jsonl"


class TestExistingConfigUnchanged:
    """Ensure existing config fields still work after additions."""

    def setup_method(self):
        get_settings.cache_clear()

    def test_anthropic_api_key_still_works(self):
        s = Settings(environment="development", anthropic_api_key="sk-test")
        assert s.anthropic_api_key == "sk-test"

    def test_claude_model_still_works(self):
        s = Settings(environment="development")
        assert s.claude_model == "claude-sonnet-4-20250514"

    def test_cors_origins_still_works(self):
        s = Settings(environment="development", cors_origins="http://a,http://b")
        assert s.get_cors_origins() == ["http://a", "http://b"]
