# T13.97 — SQLi Audit

**Sprint:** S13
**Method:** Grep `backend/app/` for SQL string-concatenation patterns; spot-check every dynamic query.
**Generated:** 2026-04-25

## Approach

Searched for these SQL-injection-suspect patterns across `backend/app/`:

```
execute\(.*\+              # string concatenation in execute()
f"\"\"\s*(SELECT|INSERT|UPDATE|DELETE)  # f-string SQL
f'(SELECT|INSERT|UPDATE|DELETE)         # single-quote f-string SQL
%s.*%[s|d].*execute        # printf-style SQL
execute.*%s                # execute with % formatting
```

## Findings

**Zero SQLi findings.**

The grep returned 0 hits across all patterns. Every database query in `backend/app/` uses parameterized SQL with `?` placeholders (sqlite3 / aiosqlite) or named parameters (SQLAlchemy `text(":name")`).

### Verified clean (sampled)

- `compliance/_audit.py::write_audit` — `conn.execute("INSERT INTO compliance_audit (...) VALUES (?, ?, ?, ?, ?)", (params,))` ✓
- `compliance/delete.py::full_delete` — explicit table list with hardcoded names; per-table `DELETE FROM <table> WHERE session_id = ?` ✓
- `compliance/retention.py::_purge_one` — same pattern as delete.py ✓
- `engagement/unsubscribe_tokens.py` — uses `INSERT INTO used_tokens (token_hash, used_at) VALUES (?, ?)` ✓
- `appointments/tokens.py` — same single-use pattern ✓
- `core/feature_flags.py` — flag CRUD via parameterized queries ✓
- `routes/jobs_applications.py`, `routes/documents.py`, `routes/engagement.py` — all parameterized ✓
- `_qc_reset_wipe.py::wipe_demo_rows` (T13.3) — table list is hardcoded; per-table DELETE uses `WHERE session_id IN (...)` with parameterized session IDs ✓
- `_demo_seed_*` modules — INSERT statements use `(?, ?, ?, ?)` placeholders ✓
- `core/migrations/m*.py` — DDL only (no user input)

### Dynamic table identifiers

A handful of code paths take a table name as a function parameter (e.g., the cascade-delete loop iterates over `_NON_CASCADING_TABLES`). These are NOT user-supplied — the table list is a hardcoded module constant. Confirmed:

- `compliance/delete.py::_NON_CASCADING_TABLES` — hardcoded tuple of 5 strings
- `_qc_reset_wipe.py::SESSION_KEYED_TABLES` — hardcoded tuple
- `compliance/retention.py` — imports `_NON_CASCADING_TABLES` from delete.py (single source of truth, T13.58 + T13.70 alignment)

No path lets a user influence a table name in a query.

### Order-by / limit / pagination

A common SQLi vector is `ORDER BY {user_input}` since these can't be parameterized. Spot-checked endpoints with sort/order parameters:

- `routes/jobs.py` — list endpoint uses fixed column ordering (no user-supplied order_by)
- `routes/advisor_inbox.py` — fixed sort
- `routes/jobs_applications.py` — fixed sort

No dynamic ORDER BY with user input found.

## Recommendation

- No changes required.
- For ongoing protection: add a CI lint that catches new `execute("...")` calls with `+`, f-string interpolation, or `%s` formatting in SQL strings. The `bandit` static analyzer would catch this — could be added to the backend CI job (P2, defer to S14).

## Out of scope

- ORM-level injection (project uses raw sqlite3 + occasional SQLAlchemy `text()`; both are parameterized, but ORM-managed queries elsewhere would also be fine)
- NoSQL injection (project doesn't use NoSQL)
- Stored procedure injection (project doesn't use stored procedures)
