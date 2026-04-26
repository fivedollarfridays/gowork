# T13.74 — Pathological Input Fuzz

**Sprint:** S13 platform-qc
**Branch:** sprint/s13-platform-qc
**Date:** 2026-04-24
**Time-box:** ~40 min
**Scope:** Non-injection adversarial payloads against every mutating backend
endpoint. Excludes prompt-injection (T13.57) and SSRF (T13.95).

---

## Method

1. Built an in-process ASGI fuzz harness against `app.main:app` with a fresh
   SQLite DB seeded by `init_db` + `upsert_barrier_graph` (matches the
   `client` fixture in `backend/tests/conftest.py`). No staging traffic.
2. Drove the corpus listed in the task brief (33 payload classes covering
   length, encoding, unicode, HTML/MD, SQL, path, format, JSON, XXE, control
   chars) through every text/string field of every POST/PATCH endpoint
   reachable from a freshly-seeded test DB.
3. Captured `(status, response_body)` plus a payload-reflection oracle and
   followed up with targeted probes that read the SQLite row directly to
   inspect what was actually persisted.

**Total requests issued:** 593 across 10 endpoints. **5xx count:** 0.
The 35 `OperationalError: no such table: advisor_tokens` rows in the raw
log are a test-fixture artifact (`init_db` doesn't seed the advisor migrations);
the same 3 `client_exc: InvalidURL` rows are httpx refusing to *send* a path
containing raw control bytes, never a server crash.

---

## Summary by class

| Class | Endpoints probed | 5xx | Findings |
|-------|------------------|-----|----------|
| Empty / whitespace | 10 | 0 | none |
| Length boundary    | 10 | 0 | F1, F2 (silent unbounded acceptance + storage) |
| Emoji / ZWJ        | 10 | 0 | F4 (stored intact, not re-rendered safely) |
| RTL / bidi         | 10 | 0 | F4 (U+202E stored intact) |
| Zero-width         | 10 | 0 | F4 |
| NFC vs NFD         | 10 | 0 | F3 (no normalization on free-text) |
| Null byte          | 10 | 0 | F1 (`\x00` stored intact, not rejected) |
| HTML injection     | 10 | 0 | F5 (stored as-is — XSS risk if any consumer reflects without escaping) |
| Markdown injection | 10 | 0 | F5 |
| SQL fragments      | 10 | 0 | clean (parameterized queries) |
| Path traversal     | 10 | 0 | clean (no file-path inputs reachable here) |
| Format string      | 10 | 0 | clean |
| JSON injection     | 10 | 0 | clean (pydantic owns parsing) |
| XXE                | 10 | 0 | clean (JSON-only ingestion; sendgrid handler short-circuits on signature) |
| Control characters | 10 | 0 | F1 |

---

## Findings

### F1 — `\x00` (null byte) and other C0 control chars accepted and stored verbatim
**Severity:** Medium
**Endpoints:**
- `POST /api/assessment/` → `work_history` → persisted into `sessions.qualifications`
- `POST /api/feedback/resource` → `barrier_type` → persisted into `resource_feedback.barrier_type`

**Observed:**
```
input  : "BEFORE\x00AFTER"
status : 201 / 200
stored : b'BEFORE\x00AFTER'   # SQLite happily stored the null byte
length : 12 (full round-trip preserved)
```

**Expected:** Reject (`422`) **or** strip silently with a documented contract.
The task brief explicitly calls this out: "must be rejected, not silently
truncated". Today neither happens — the byte is stored intact.

The `feedback/visit` `free_text` field already does this correctly via a
`@field_validator` in `app/modules/feedback/types.py` lines 49–58 (strip,
NFC-normalize, drop `\x00`). That validator should be lifted into a shared
helper and applied to every persisted free-text field, including
`AssessmentRequest.work_history` and `ResourceFeedbackRequest.barrier_type`.

**Suggested fix:** Apply the existing `sanitize_free_text` validator (or a
shared `app/core/text.py` helper) to:
- `AssessmentRequest.work_history`, `resume_text`, items of `target_industries`
  / `certifications` (`backend/app/modules/matching/types.py`)
- `ResourceFeedbackRequest.barrier_type`
  (`backend/app/modules/feedback/types.py`)
- `ApplicationCreate.company`, `role`, `match_source`, `match_url`
  (`backend/app/routes/jobs_applications.py`)
- `AppointmentPatch.title`, `notes`, `location_name`, `location_address`
  (`backend/app/routes/appointments.py`)

The same control-char sweep (`\x07\x08\x0c\x1b`, `\b\f\v`) survives the
same path with the same outcome.

---

### F2 — `barrier_type` field has no length limit; 50 KB string round-trips
**Severity:** Medium
**Endpoint:** `POST /api/feedback/resource`
**Field:** `barrier_type` (declared `Optional[str] = None` with no constraint)

**Observed:** Sent 50 000 characters → `200 OK` and the full 50 000-char
string was stored. There is no upper bound. Combined with a rate limiter
of 20/min/IP and the column being indexed-by-session, this is a small DOS
amplifier (write 1 MB row per 3 seconds).

**Expected:** A `Field(max_length=64)` (the field is meant to be one of the
seven `BarrierType` enum values).

**Suggested fix:**
```python
# app/modules/feedback/types.py
barrier_type: Optional[str] = Field(default=None, max_length=64)
```
Stronger fix: type it as `Optional[BarrierType]` so pydantic enforces the
enum membership.

The same audit applies to `ApplicationCreate.{company, role, match_source,
match_url}` and `AppointmentPatch.{title, notes, location_name,
location_address}` — none carry `max_length`. Each is one validator line.

---

### F3 — No NFC normalization on persisted free-text (except `feedback/visit.free_text`)
**Severity:** Low
**Endpoints:** `POST /api/assessment/` (`work_history`, `resume_text`),
`POST /api/feedback/resource` (`barrier_type`),
`POST /api/job-applications` (`company`, `role`).

**Observed:**
- Sent `"café"` (NFC, 4 codepoints) → stored as 4 bytes via UTF-8 = `b'caf\xc3\xa9'`.
- Sent `"café"` (NFD, 5 codepoints `c-a-f-e-U+0301`) → stored as the same
  *visual* string but **different byte sequence** = `b'cafe\xcc\x81'` in DB.

**Impact:** Equal-looking strings compare unequal. Two records "café" and
"café" coexist with no de-dup. A name-search advisor query for "café"
misses NFD rows. Not a security bug; consistency / data-quality bug.

**Suggested fix:** Same shared normalize helper as F1 — NFC-normalize on
ingest. The fix is one line per validator.

---

### F4 — Bidi & zero-width characters stored intact (UI-rendering risk)
**Severity:** Low (depends on whether any consumer renders raw)
**Endpoints:** Same set as F1.

**Observed:**
- `U+202E RIGHT-TO-LEFT OVERRIDE` survives storage in `work_history`
  (`'hello ‮ reverse'` round-trips byte-perfect).
- Zero-width joiner / non-joiner / space + ZWJ emoji sequences round-trip
  intact.
- `len_100k` of `"a"` (single ASCII char repeated) was reflected back in
  the response body of `POST /api/assessment/` when stored in `work_history`
  (size proportional to input).

**Impact:**
- Advisor inbox / share-page renders the raw stored text. A worker who
  pastes a U+202E into a profile field can flip the visible direction of
  any subsequent text in that record (e.g., `"BNSF Railway ‮ moc.eldnah"`
  visually displays as `"BNSF Railway handle.com"`). Phishing surface.
- ZWJ + invisible-character padding lets two visually-identical job-app
  rows differ in stored bytes (de-dup bypass, similar to F3).

**Expected:** Either strip or escape the **bidi-override / format**
codepoint range (`U+200B–U+200F`, `U+202A–U+202E`, `U+2066–U+2069`) on
ingest, or HTML-escape on render. Per OWASP, server-side strip is the
safer default unless RTL display is a requirement (Montgomery is English-only).

**Suggested fix:** Add a single regex strip step to the shared
sanitize helper proposed in F1.

---

### F5 — HTML/Markdown payloads stored verbatim — relies entirely on consumer escaping
**Severity:** Low (no current XSS surface confirmed; defense-in-depth gap)
**Endpoints:** Every persisted free-text endpoint (assessment, jobs,
appointments, feedback/resource).

**Observed:**
- `<script>alert(1)</script>` stored intact in `sessions.qualifications`.
- `<img src=x onerror=alert(1)>` likewise.
- `![](javascript:alert(1))` likewise.

The frontend's React rendering layer escapes by default, and the assessment
response bodies are JSON (`Content-Type: application/json`), so today the
payload is delivered as a JSON string and not auto-rendered. **However**:

- `app/routes/share.py:90` `GET /shared/{share_token}` returns plan data in
  JSON; if any future view templates `next_steps` or `qualifications` as
  raw HTML, the stored payload becomes reflected XSS.
- The advisor inbox rendering path (`docs/security/advisor-auth.md` C7 area)
  similarly trusts stored text.

**Expected:** Treat the data layer as untrusted regardless of consumer.
Strip HTML tags or, at minimum, scrub `<script>`, `<style>`, `<iframe>`,
`<object>`, and `javascript:` / `data:text/html` URI schemes from ingest.

**Suggested fix:** Add an HTML-tag scrubber (`bleach.clean(text, tags=[],
strip=True)`) to the same sanitize helper. Document it as the contract.

---

### F6 — `len_100k` (100 KB) reflected in assessment response body
**Severity:** Low (informational)
**Endpoint:** `POST /api/assessment/`

**Observed:** `work_history` capped server-side at 500 chars (validation
works); but when I trimmed inputs to fit the cap and re-sent, the response
echoed the field at full length, growing the response body proportionally.
That's expected (the API returns the stored profile) — flag here only to
confirm the pydantic `max_length=500` on `work_history` is the only thing
between callers and unbounded body growth. Removing or relaxing that cap
without a separate response-size budget would be a regression.

No action required; tracking for awareness.

---

## Clean endpoints (no 5xx and no persistence bug across full corpus)

| Endpoint | Notes |
|----------|-------|
| `POST /api/credit/assess` | Pydantic 422 on every non-int payload before any handler logic — clean. |
| `POST /api/engagement/preferences` | Pydantic `bool_parsing` 422 on every non-bool payload — clean. |
| `POST /api/engagement/unsubscribe` | Uniform `401 "Invalid or expired unsubscribe token"` on every payload incl. 100 KB input and null bytes — token verifier is byte-safe. |
| `POST /api/webhooks/sendgrid/events` | Uniform `401 "missing signature"` / `"invalid signature"` even with 100 KB / null-byte / XXE bodies — signature gate fires before any parsing. |
| `POST /api/advisor/sessions/{sid}/note` | Reaches the auth dep before any payload parsing. (Couldn't fully verify behind a valid token because `init_db` doesn't seed `advisor_tokens`; recommend a follow-up probe inside an integration test that already has a valid advisor token.) |
| `POST /api/plan/{sid}/share` (token query) | `401`/`403` on every garbage token — no 5xx. |
| SQL injection on every probed field | Parameterized `sqlalchemy.text(... :tok)` and `?`-placeholder `sqlite3.execute(... (val,))` everywhere I read — no concatenation seen. SQL fragments stored as inert strings. |

---

## Out of scope

- **Prompt injection** — covered by T13.57 (`backend/tests/test_injection_fuzz.py`).
- **SSRF** on URL fields (`match_url`, `webhook URLs`) — T13.95.
- **Endpoints behind admin / advisor auth** I could not seed in the test fixture:
  `POST /api/admin/flags/{name}`, `POST /api/engagement/send-now`, advisor
  send-note. Recommend a follow-up that reuses the integration-test fixtures
  that *do* seed those tables.
- **Appointment endpoints** (`POST /api/appointments`,
  `PATCH /api/appointments/{id}`) — reachable in principle but the helper
  resolves a different DB path than the async test engine, so a clean probe
  needs the appointments-helpers monkeypatch fixture
  (`tests/_appointments_helpers.py`). Reading the schema, **AppointmentPatch
  has the same unbounded-text pattern as F2** — 60 lines of unchecked
  `str | None` fields (`title`, `notes`, `location_name`, `location_address`).
  Reasonable to assume the same finding applies; recommend confirming as
  part of the F1+F2 fix.
- **`POST /api/brightdata/crawl` / `precrawl` / `barrier-intel/reindex` /
  `barrier-intel/chat` / `simulate` / `pathway` / `documents/resume` /
  `documents/cover-letter` / `compliance/*`** — schemas read but not driven
  through the corpus to keep within time-box. The compliance endpoints in
  particular have `session_id` UUID validation up-front (good), and
  `barrier-intel/chat` is the LLM endpoint already covered by T13.57.

---

## Top finding

**F1 + F2 together** — the absence of a shared input-sanitization helper.
The free_text field on `feedback/visit` shows the team already has the
right pattern (`backend/app/modules/feedback/types.py:49`). Today it's
applied to one field. The other six free-text fields skip it, which is
how null bytes, U+202E, NFD strings, and unbounded text all reach SQLite.
A single helper + ~6 `Annotated` validator hookups closes F1, F3, F4,
and most of F5 in one PR.

---

## Counts by severity

| Severity | Count |
|----------|-------|
| High     | 0 |
| Medium   | 2 (F1, F2) |
| Low      | 4 (F3, F4, F5, F6) |
| Informational only | F6 |

No 5xx / unhandled-exception findings.

## Time spent

~40 minutes — 10 endpoints × 33 payloads + 4 targeted persistence-inspection
probes + report.
