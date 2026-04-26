# T13.94 — PII Log Scrub Audit

**Sprint:** S13
**Method:** Grep across `backend/app/` for `logger.{info,warning,error,exception,debug}` calls; filter to PII-suspect patterns (`session_id`, `to_email`, `phone`, name fields).
**Generated:** 2026-04-25
**Cross-reference:** T13.59 (advisor_inbox PII fix), `compliance/_audit.hash_session_id`, `core/logging.py`

## Logging infrastructure summary

- **Library:** `structlog` (configured in `backend/app/core/logging.py`)
- **Output:** stdout (JSON in production via `ENVIRONMENT=staging|production`; human-readable in dev)
- **Existing PII redactor:** **None centralized.** Hashing is done at the call site via `compliance._audit.hash_session_id`, not by a structlog processor.
- **Recommendation:** add a structlog processor that redacts known-PII keys at the EVENT level (any field named `session_id`, `email`, `phone` gets hashed/redacted before serialization). One module, no per-call-site discipline required.

## Findings

### M — Two raw-`session_id` log calls in `routes/career_center.py`

```
backend/app/routes/career_center.py:59:
    logger.warning("Invalid credit profile data for %s", session_id)
backend/app/routes/career_center.py:73:
    logger.warning("Using fallback profile for session %s (stored profile missing/corrupt)", session_id)
```

- **Issue:** raw `session_id` (UUID) emitted in a structured warning. T13.59 fixed the equivalent in `advisor_inbox`; this one was missed.
- **Severity:** Medium — structlog runs at WARNING level even in prod; logs aggregate into stdout → Fly's log drain → wherever drained. Persistent identifier in logs is the same exposure class T13.59 closed.
- **Fix:** wrap both with `hash_session_id(session_id)` at the call site (or, better, install the centralized scrubber so future call sites get coverage automatically).

### Verified clean (sampled)

- `routes/compliance.py` — uses `hash_session_id` for filename + audit
- `routes/advisor_inbox.py` — fixed in T13.59 (now logs `session_id_hash`)
- `routes/engagement.py` — logs only error-class names + counts
- `routes/appointments_manage.py` — logs `error_class` + appointment_id (numeric, not PII)
- `routes/documents.py` — `logger.exception(...)` with extra metadata, no PII fields
- `core/scheduler_jobs.py`, `modules/orchestrator/*` — logs counts + module names, no per-session detail
- `modules/engagement/reminder_engine.py` — logs send counts + error-class, NOT recipient emails

## Recommended remediation (one-line summary)

Add to `backend/app/core/logging.py` a structlog processor:

```python
def _scrub_pii(_logger, _method_name, event_dict):
    for key in ("session_id", "to_email", "from_email", "phone", "actor_email"):
        if key in event_dict and event_dict[key]:
            event_dict[f"{key}_hash"] = hash_session_id(event_dict.pop(key))
    return event_dict
```

Add `_scrub_pii` to `structlog.configure(processors=[..., _scrub_pii, ...])` between context-vars and renderer. This catches every future log site without per-author discipline. The 2 outstanding `career_center.py` sites then become trivial — change `%s` to a structured `session_id=session_id` kwarg and the scrubber handles the rest.

## Out of scope

- Sentry / external observability sinks (T13.121 cancelled — hackathon scope)
- Debug-level logs (gated behind `LOG_LEVEL=DEBUG`, never enabled in prod)
- Audit ROW writes (T13.59 covered — these go to DB, not logs, and use `hash_session_id`)
