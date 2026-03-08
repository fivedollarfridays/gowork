# Barrier Intelligence Assistant

AI-powered assistant on the `/plan` page that answers user questions about their employment barriers, recommended actions, and Montgomery resources.

## API Contract

### POST /api/barrier-intel/chat

Streaming chat endpoint with Server-Sent Events (SSE).

**Request:**
```json
{
  "session_id": "uuid-string",
  "user_question": "What should I do first?",
  "mode": "next_steps"
}
```

- `mode`: `"next_steps"` (action-oriented) or `"explain_plan"` (why-based)
- `user_question`: 1-1000 characters

**Response:** `text/event-stream` with events:
```
data: {"type": "context", "root_barriers": ["CREDIT_LOW_SCORE"], "chain": "..."}

data: {"type": "token", "text": "First"}
data: {"type": "token", "text": ", you"}

data: {"type": "done", "usage": {"input_tokens": 500, "output_tokens": 200}, "latency_ms": 850}
```

**Guardrails:** If the question matches disallowed topics (legal/medical/immigration/financial advice), returns JSON instead of SSE:
```json
{"message": "I'm not able to help with that topic...", "guardrail_triggered": true}
```

**Rate limit:** 10 requests/minute per IP.

### POST /api/barrier-intel/reindex

Admin-only endpoint to rebuild the RAG index. Requires `X-Admin-Key` header.

## Caching Strategy

### v1: In-Memory (Current)

Uses `cachetools.TTLCache`:

| Cache | TTL | Max Size | Key |
|-------|-----|----------|-----|
| LLM responses | 300s (5 min) | 200 | SHA256(session_id + question + mode)[:16] |
| Retrieval context | 600s (10 min) | 500 | Same key format |

Cache hit returns the stored response immediately with `"cached": true` in the context event.

### v2: Redis (Future)

For multi-worker deployments, replace `TTLCache` with Redis:
- Same key format, same TTLs
- Enables shared cache across workers
- Add `REDIS_URL` to settings
- Replace `cachetools` imports with `aioredis` calls

## Architecture

```
User Question → Guardrails → Cache Check
                                ↓ miss
                    Retrieve Context (graph + FAISS)
                                ↓
                    Stream LLM Response (Claude)
                                ↓
                    Cache Response → SSE to Client
```

### Components

| Module | Purpose |
|--------|---------|
| `barrier_intel/router.py` | HTTP endpoints |
| `barrier_intel/streaming.py` | SSE formatting + Claude streaming |
| `barrier_intel/guardrails.py` | Topic filter + hallucination check |
| `barrier_intel/prompts.py` | System prompt + context serialization |
| `barrier_intel/cache.py` | TTL cache for responses + retrieval |
| `barrier_intel/observability.py` | Structured logging helpers |
| `rag/retrieval.py` | Hybrid retrieval (graph + vector) |
| `rag/store.py` | FAISS index singleton |

## Evaluation

### Golden Queries

`data/eval/golden_queries.json` contains 22 test queries covering:
- All barrier categories (credit, transportation, childcare, housing, certification, digital literacy, substance recovery, criminal record, employment gap)
- Both modes (next_steps, explain_plan)
- Single and multi-barrier scenarios

### Running Evaluation

```bash
# Dry run (schema validation only)
python scripts/run_eval.py --queries data/eval/golden_queries.json --dry-run

# Full evaluation (requires ANTHROPIC_API_KEY)
python scripts/run_eval.py --queries data/eval/golden_queries.json --output eval_results.json
```

### Automated Checks

Each query is evaluated on:
1. **Barrier mention:** Response references at least one expected barrier keyword
2. **No disallowed content:** Response avoids prohibited phrases
3. **Step count:** For next_steps mode, response has numbered steps within expected range
4. **Resource grounding:** Resource names in response match retrieval context

Target: ≥85% pass rate.

## Observability

Each request logs a structured entry:
```json
{
  "session_hash": "abc123def456",
  "mode": "next_steps",
  "root_barriers": ["CREDIT_LOW_SCORE"],
  "retrieval_doc_count": 3,
  "retrieval_latency_ms": 15.2,
  "llm_latency_ms": 850.0,
  "input_tokens": 500,
  "output_tokens": 200,
  "cache_hit": false,
  "guardrail_triggered": false
}
```

Session IDs are hashed (SHA256, truncated) to avoid PII in logs.
