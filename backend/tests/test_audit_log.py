"""Tests for PII-safe LLM audit logging."""

import hashlib
import json
import os

import pytest

from app.ai.audit_log import hash_session_id, log_llm_interaction


class TestHashSessionId:
    """Session IDs must be hashed with sha256 before logging."""

    def test_returns_hex_digest(self):
        result = hash_session_id("session-abc-123")
        assert isinstance(result, str)
        assert len(result) == 64  # sha256 hex length

    def test_consistent_hashing(self):
        a = hash_session_id("same-id")
        b = hash_session_id("same-id")
        assert a == b

    def test_different_ids_produce_different_hashes(self):
        a = hash_session_id("id-1")
        b = hash_session_id("id-2")
        assert a != b

    def test_matches_stdlib_sha256(self):
        raw = "test-session-xyz"
        expected = hashlib.sha256(raw.encode()).hexdigest()
        assert hash_session_id(raw) == expected


class TestLogLlmInteraction:
    """Test JSONL audit log entries."""

    def test_writes_jsonl_line(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        log_llm_interaction(
            log_path=str(log_path),
            session_id="raw-session-id",
            provider="anthropic",
            prompt_length=150,
            response_length=300,
            latency_ms=450.5,
        )
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert "timestamp" in entry
        assert entry["provider"] == "anthropic"
        assert entry["prompt_length"] == 150
        assert entry["response_length"] == 300
        assert entry["latency_ms"] == 450.5

    def test_session_id_is_hashed(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        raw_id = "raw-session-id"
        log_llm_interaction(
            log_path=str(log_path),
            session_id=raw_id,
            provider="mock",
            prompt_length=100,
            response_length=200,
            latency_ms=10.0,
        )
        entry = json.loads(log_path.read_text().strip())
        # Must NOT contain raw session ID
        assert raw_id not in json.dumps(entry)
        # Must contain hashed version
        expected_hash = hashlib.sha256(raw_id.encode()).hexdigest()
        assert entry["hashed_session"] == expected_hash

    def test_no_pii_in_log(self, tmp_path):
        """Log entries must not contain user prompts or response text."""
        log_path = tmp_path / "audit.jsonl"
        log_llm_interaction(
            log_path=str(log_path),
            session_id="user-session",
            provider="openai",
            prompt_length=500,
            response_length=1200,
            latency_ms=800.0,
        )
        raw_text = log_path.read_text()
        entry = json.loads(raw_text.strip())
        # Only metadata fields allowed
        allowed_keys = {"timestamp", "hashed_session", "provider", "prompt_length", "response_length", "latency_ms"}
        assert set(entry.keys()) == allowed_keys

    def test_appends_multiple_entries(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        for i in range(3):
            log_llm_interaction(
                log_path=str(log_path),
                session_id=f"session-{i}",
                provider="mock",
                prompt_length=100 + i,
                response_length=200 + i,
                latency_ms=float(i * 10),
            )
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 3
        # Each line is valid JSON
        for line in lines:
            json.loads(line)

    def test_creates_parent_dirs(self, tmp_path):
        log_path = tmp_path / "subdir" / "deep" / "audit.jsonl"
        log_llm_interaction(
            log_path=str(log_path),
            session_id="session",
            provider="mock",
            prompt_length=10,
            response_length=20,
            latency_ms=5.0,
        )
        assert log_path.exists()

    def test_skips_when_no_log_path(self):
        """Should not raise when log_path is empty string."""
        log_llm_interaction(
            log_path="",
            session_id="session",
            provider="mock",
            prompt_length=10,
            response_length=20,
            latency_ms=5.0,
        )
        # No exception = pass

    def test_timestamp_is_iso_format(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        log_llm_interaction(
            log_path=str(log_path),
            session_id="session",
            provider="gemini",
            prompt_length=100,
            response_length=200,
            latency_ms=50.0,
        )
        entry = json.loads(log_path.read_text().strip())
        # ISO format contains 'T' separator
        assert "T" in entry["timestamp"]
