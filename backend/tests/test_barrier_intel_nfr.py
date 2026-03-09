"""Tests for barrier intelligence NFRs: caching, observability, extended health."""

import hashlib
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.barrier_intel.cache import (
    RESPONSE_CACHE,
    RETRIEVAL_CACHE,
    get_cache_key,
    get_cached_response,
    set_cached_response,
    get_cached_retrieval,
    set_cached_retrieval,
)
from app.barrier_intel.observability import build_request_log


class TestCacheKey:
    def test_deterministic(self):
        k1 = get_cache_key("sess1", "What next?", "next_steps")
        k2 = get_cache_key("sess1", "What next?", "next_steps")
        assert k1 == k2

    def test_different_inputs_different_keys(self):
        k1 = get_cache_key("sess1", "What next?", "next_steps")
        k2 = get_cache_key("sess2", "What next?", "next_steps")
        k3 = get_cache_key("sess1", "Why?", "next_steps")
        k4 = get_cache_key("sess1", "What next?", "explain_plan")
        assert len({k1, k2, k3, k4}) == 4


class TestResponseCache:
    def setup_method(self):
        RESPONSE_CACHE.clear()

    def test_miss_returns_none(self):
        assert get_cached_response("nonexistent") is None

    def test_set_and_get(self):
        set_cached_response("key1", "Hello response")
        assert get_cached_response("key1") == "Hello response"

    def test_cache_stores_dict(self):
        data = {"message": "test", "context": {"root": []}}
        set_cached_response("key2", data)
        assert get_cached_response("key2") == data


class TestRetrievalCache:
    def setup_method(self):
        RETRIEVAL_CACHE.clear()

    def test_miss_returns_none(self):
        assert get_cached_retrieval("nonexistent") is None

    def test_set_and_get(self):
        ctx = {"root_barriers": ["CREDIT"], "docs": []}
        set_cached_retrieval("key1", ctx)
        assert get_cached_retrieval("key1") == ctx


class TestObservability:
    def test_build_request_log_structure(self):
        log = build_request_log(
            session_hash="abc123def456",
            mode="next_steps",
            root_barriers=["CREDIT_LOW_SCORE"],
            retrieval_doc_count=3,
            retrieval_latency_ms=15.2,
            llm_latency_ms=850.0,
            prompt_chars=500,
            response_chars=200,
            cache_hit=False,
            guardrail_triggered=False,
        )
        assert log["session_hash"] == "abc123def456"
        assert log["mode"] == "next_steps"
        assert log["cache_hit"] is False
        assert log["guardrail_triggered"] is False
        assert log["retrieval_doc_count"] == 3

    def test_build_request_log_with_cache_hit(self):
        log = build_request_log(
            session_hash="abc",
            mode="explain_plan",
            root_barriers=[],
            retrieval_doc_count=0,
            retrieval_latency_ms=0,
            llm_latency_ms=0,
            prompt_chars=0,
            response_chars=0,
            cache_hit=True,
            guardrail_triggered=False,
        )
        assert log["cache_hit"] is True


class TestHealthExtended:
    @pytest.mark.anyio
    async def test_health_includes_rag_store(self, client, test_engine):
        from app.main import app
        from app.rag.store import RagStore

        store = RagStore()
        app.state.rag_store = store
        resp = await client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] in ("healthy", "degraded")

    @pytest.mark.anyio
    async def test_ready_includes_rag_check(self, client, test_engine):
        from app.main import app
        from app.rag.store import RagStore

        store = RagStore()
        app.state.rag_store = store
        resp = await client.get("/health/ready")
        assert resp.status_code in (200, 503)
        body = resp.json()
        check_names = [c["name"] for c in body["checks"]]
        assert "rag_store" in check_names


class TestGoldenQueriesSchema:
    def test_golden_queries_file_valid(self):
        with open("data/eval/golden_queries.json") as f:
            queries = json.load(f)
        assert len(queries) >= 20
        for q in queries:
            assert "id" in q
            assert "situation" in q
            assert "question" in q
            assert "mode" in q
            assert q["mode"] in ("next_steps", "explain_plan")
            assert "expected_properties" in q
            sit = q["situation"]
            assert "barriers" in sit
            assert len(sit["barriers"]) >= 1

    def test_golden_queries_cover_barrier_variety(self):
        with open("data/eval/golden_queries.json") as f:
            queries = json.load(f)
        all_barriers = set()
        for q in queries:
            all_barriers.update(q["situation"]["barriers"])
        assert len(all_barriers) >= 5
