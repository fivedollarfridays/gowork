# Advisor Auth Model (T12.31a)

> Runbook for advisor identity, city-scoped authorization, token issuance,
> rotation, and incident response. Prerequisite to **T12.31** (advisor inbox
> endpoints). Mirrors the structure of
> `docs/ops/appointment-token-rotation.md` so operators can cross-reference
> the two signing-key playbooks without context-switching.

## 1. Overview

The advisor role gives case managers scoped access to stalled-session detail
so they can intervene on workers who submitted outcomes but went silent.
Advisors see cleared-record PII (charge categories, years-since-conviction,
employer rejection reasons) — data that must never cross city boundaries.
Unlike the single-key admin role (`require_admin_key`), every advisor token
is bound to exactly one city and every backing query is filtered by that
city. Cross-city access is a hard-denial failure (HTTP 403), not an
empty-result soft-fail.

This document makes the **design call** for advisor auth, documents the
operational lifecycle (issuance, rotation, revocation, incident response),
and specifies the backend enforcement contract every advisor-scoped
endpoint must honour. T12.31 implements against this contract.

---

## 2. Identity Model

### Single-advisor-per-city? Many-to-many?

**Decision — one advisor per token, one city per token, many advisors per
city allowed.**

- An advisor token row carries exactly one `advisor_id` and exactly one
  `city`. No list-of-cities column.
- A human advisor who covers two cities is issued two separate tokens —
  one per city — and switches `X-Admin-Key` between them. The token is
  the unit of authorisation, not the person.
- A single city may have multiple active advisor tokens (e.g. a primary
  advisor plus a backup during PTO). There is no uniqueness constraint
  on `city` in `advisor_tokens`.

### Rationale

- **Blast-radius control.** One compromised token = one compromised
  city, never multi-city. The alternative (list-of-cities per token)
  turns every revocation into a multi-table mutation.
- **Audit clarity.** Every `engagement_events` row for
  `category='advisor_action'` resolves to a single `(advisor_id_hash,
  city)` pair — no ambiguity about which seat performed the action.
- **Operational simplicity.** Issuance is a linear bash command; no
  JSON-array claim-mangling.

### Not supported (deferred)

- Multi-city tokens with per-row ACL — would require a `cities TEXT[]`
  column plus a `city IN (?)` rewrite at every repository layer. Out of
  scope for S12b.
- SSO / IdP federation — no OIDC integration; advisor tokens are bearer
  secrets issued by operators.
- Fine-grained per-session permissions — advisors have all-or-nothing
  access within their city.

---

## 3. Option Comparison

### Option A — Extend `require_admin_key` with per-advisor tokens + `city` claim

Add a new `advisor_tokens(token_hash, advisor_id, city, issued_at,
revoked_at)` table. The existing `X-Admin-Key` header is reused, but the
new dependency `require_advisor_token` returns `(advisor_id, city)`
instead of a boolean admin check. Token issuance writes a row; revocation
sets `revoked_at`.

### Option B — Distinct `AdvisorToken` system

A new header `X-Advisor-Token`, a separate verification pipeline, a
separate rate-limiter, a separate audit hook. Clean separation at the
cost of duplicated plumbing.

### Trade-off Table

| Dimension                   | Option A (extend admin key)                                   | Option B (distinct AdvisorToken)                                     |
|-----------------------------|---------------------------------------------------------------|----------------------------------------------------------------------|
| Lines of new code           | Low (~150 — new table, new dependency, reuse rate-limiter)    | High (~400 — separate header, verifier, rate-limiter, audit wiring)  |
| Header namespace            | Shared with admin — requires careful dependency wiring        | Distinct `X-Advisor-Token` header — no collision                     |
| Rate-limit reuse            | Reuses `_check_rate_limit` + `hash_actor_token` from T12.0b   | Must duplicate or refactor rate-limiter to a shared module           |
| Audit hook reuse            | Reuses `hash_actor_token` pattern for `advisor_id_hash`       | Duplicated hashing code path                                         |
| Rotation plumbing           | Per-token revocation (row-level `revoked_at`); no HMAC secret | HMAC-signed token (kid + rotation window) — reuses T12.10b pattern   |
| Privilege-escalation risk   | Admin key and advisor tokens share a header — wiring-critical | Impossible by construction (different headers, different dependency) |
| Observability granularity   | Admin and advisor actions co-mingled in same audit stream     | Separate audit stream per token type                                 |
| Fit for current scale       | Excellent (5 cities, <20 advisors projected)                  | Over-engineered for current scale                                    |
| Fit at 10x scale            | Adequate — would grow table + add rate-limiter per-token      | Cleaner — each concern has its own module                            |

---

## 4. Chosen Option

### **Option A — extend `require_admin_key` with per-advisor tokens + `city` claim.**

**Rationale:**

1. **Reuses existing plumbing.** The admin-key header pipeline in
   `backend/app/core/auth.py` already handles FastAPI header extraction,
   constant-time compare, and 503-when-unconfigured. T12.0b + T12.21
   already built rate-limiting (`_check_rate_limit`, `hash_actor_token`)
   on top of that. Option A adds exactly one lookup step — "does this
   key match a non-revoked row in `advisor_tokens`?" — before returning
   `(advisor_id, city)`.
2. **Scale-appropriate.** Today: 2 cities live (Montgomery,
   Fort Worth), 5 cities projected for S13. A handful of advisor tokens
   per city. Option B's dedicated module buys clean separation we do not
   need yet.
3. **Audit parity.** The existing admin audit pattern
   (`hash_actor_token` → `engagement_events`) drops straight in as
   `advisor_id_hash` without a new hashing path.
4. **Low privilege-escalation risk when wired correctly.** The two
   dependencies (`require_admin_key`, `require_advisor_token`) never
   overlap on a route — admin routes use the first, advisor routes use
   the second. Mechanical review is tractable.

### When to reconsider (reopen for Option B)

- Advisor count exceeds ~50 tokens (rate-limit bucket contention on a
  shared actor-hash keyspace becomes a real concern).
- An advisor SSO / IdP integration becomes a requirement (Option A's
  opaque bearer token cannot carry federated claims).
- A compliance review requires distinct audit streams for admin vs.
  advisor actions (e.g. SOC 2 control mapping).
- The admin key itself needs rotation to HMAC-signed format — at which
  point T12.10b's pattern becomes the natural foundation and a distinct
  `AdvisorToken` module is cheaper than retrofitting.

---

## 5. Token Format and Claims

### Wire format

```
mw_adv_<32-character base58>
```

- Prefix `mw_adv_` makes advisor tokens instantly distinguishable from
  the admin key in audit greps, secret-scanner hits, and incident logs.
- Body: 32 base58 characters = ~192 bits of entropy. Base58 avoids
  ambiguous glyphs (`0`, `O`, `I`, `l`) that break tokens in screenshots
  and paste buffers.

### Claims — stored server-side in `advisor_tokens` row

| Column        | Type               | Purpose                                                               |
|---------------|--------------------|-----------------------------------------------------------------------|
| `token_hash`  | TEXT PRIMARY KEY   | SHA256 of the plaintext token. Plaintext never persisted.             |
| `advisor_id`  | TEXT NOT NULL      | Opaque operator-assigned id (e.g. `adv-jane-mtg`). Hashed at audit.   |
| `city`        | TEXT NOT NULL      | The single `city` claim — enforced on every query.                    |
| `issued_at`   | TIMESTAMP NOT NULL | Creation timestamp. UTC ISO-8601.                                     |
| `revoked_at`  | TIMESTAMP NULL     | NULL = active. Non-NULL = revoked (effective immediately).            |
| `expires_at`  | TIMESTAMP NULL     | Optional hard expiry. NULL = no time-based expiry, rotation-only.     |

### City-binding claim

- The `city` column IS the claim. It is a string that matches
  `outcomes_records.payload_json.city` and (future) `sessions.city`.
- The value is set at issuance and **never mutated**. A change of scope
  (e.g. advisor transfers cities) requires: revoke old row, issue new
  row. No `UPDATE advisor_tokens SET city = ?`.

### Why a server-side row instead of an HMAC-signed payload?

We considered mirroring T12.10b's HMAC-signed token (kid + rotation
window + stateless payload). For advisor auth we picked server-side
storage because:

- **Instant revocation is required.** Signed tokens with a 7-day TTL
  cannot be revoked mid-flight without a blocklist table; a blocklist
  table is just a worse version of `advisor_tokens.revoked_at`.
- **Low volume.** Advisor tokens are read once per request against a
  table with <100 rows. The lookup cost is negligible.
- **No forwardable payload.** Appointment tokens ride in email URLs
  where server-roundtrip-per-link is undesirable. Advisor tokens ride
  in `X-Admin-Key` over TLS; the roundtrip is a non-issue.

---

## 6. Token Issuance and Storage

### Issuance — operator CLI (proposed)

```bash
bpsai-pair advisor issue \
  --city montgomery \
  --advisor-id adv-jane-mtg \
  --expires 2027-04-01
```

Output:

```
Issued advisor token for adv-jane-mtg (city=montgomery).

  mw_adv_9aP7kDxRv2mLq8sJ4tN1bYwE6cHfZ0uT

Copy this ONCE. It will not be shown again. If lost, re-issue.
```

### Manual fallback (S12b, before CLI ships)

Until the CLI lands, a DBA issues tokens via SQL:

```bash
# Generate plaintext on a trusted workstation
python3 -c "import secrets; print('mw_adv_' + secrets.token_urlsafe(24))"
```

Then in the prod DB:

```sql
INSERT INTO advisor_tokens (token_hash, advisor_id, city, issued_at)
VALUES (
  -- SHA256 hex of the plaintext above, computed on the same workstation:
  --   echo -n "<plaintext>" | shasum -a 256
  '<sha256-hex>', 'adv-jane-mtg', 'montgomery', CURRENT_TIMESTAMP
);
```

The plaintext is communicated to the advisor out-of-band (encrypted
email, 1Password share link, etc.) and then destroyed on the
workstation.

### Storage rules

- **Plaintext token is never persisted** — only `SHA256(plaintext)` hits
  the DB.
- Plaintext is never logged. Every code path that accepts the token
  must pass it directly into `sha256_hex(...)` and discard.
- The `X-Admin-Key` request header is not logged at INFO. If DEBUG
  logging captures headers in development, it must scrub `X-Admin-Key`
  before emit (existing precedent — see `admin_flags.py` logger
  filters).

---

## 7. Rotation Policy

### Defaults

| Parameter            | Value                                                        |
|----------------------|--------------------------------------------------------------|
| Default lifetime     | 1 year from `issued_at`                                      |
| Rotation cadence     | Every 6 months, per advisor                                  |
| Overlap window       | None (row-level revocation is instant)                       |
| Per-request TTL check| `expires_at` if set; no HMAC-level TTL (not a signed token)  |
| Compromise response  | Immediate revocation + re-issuance (see Section 9)           |

### Planned rotation (no active incident)

Unlike HMAC-signed tokens (T12.10b), advisor tokens rotate one at a
time, per advisor:

1. Issue the new token using the CLI (or SQL fallback). Hand it to the
   advisor out-of-band.
2. Have the advisor confirm the new token works on a harmless endpoint
   (e.g. `GET /api/case-manager/sessions?city=<city>` returns 200).
3. Revoke the previous token:
   ```sql
   UPDATE advisor_tokens
      SET revoked_at = CURRENT_TIMESTAMP
    WHERE advisor_id = 'adv-jane-mtg'
      AND revoked_at IS NULL
      AND token_hash <> '<new-token-sha256>';
   ```
4. Log the rotation in the infra change log (timestamp, advisor_id,
   operator, reason = "planned 6-month rotation").

**No validation-window.** Because rotation is row-level, there is no
need to run the old and new secret in parallel. The advisor simply
switches headers the moment step 2 completes.

### Why no HMAC-style rotation window?

Appointment tokens (T12.10b) rotate via dual-secret overlap because
thousands of outstanding tokens ride in email inboxes. Advisor tokens
have a population of ~1 live plaintext per advisor, held by one person,
and are always replaced 1:1. A rotation window would be security debt,
not security value.

---

## 8. Revocation

### How to revoke

```sql
UPDATE advisor_tokens
   SET revoked_at = CURRENT_TIMESTAMP
 WHERE advisor_id = 'adv-jane-mtg';
```

### Time-to-revoke SLA

- **Target: under 5 minutes** from decision to effective. The dependency
  re-reads the row on every request (no caching); the moment the UPDATE
  commits, the next request with that token gets 401.
- For a bulk / scripted compromise (multiple advisors), revoke all
  affected rows in a single transaction.

### What to do after revocation

- Log the revocation to the infra change log: timestamp, advisor_id,
  operator, reason.
- Re-issue a fresh token if the advisor still needs access (standard
  issuance flow — the revoked row stays in the table for audit).
- Purge the plaintext from any shared-secret manager entry that may
  have been used to deliver it.

### What NOT to do

- **Do not delete the row.** `revoked_at` preserves audit continuity.
  Deletion hides the fact that the token ever existed.
- **Do not `UPDATE ... SET city = ?` to "relocate" an advisor.** Revoke,
  then issue fresh — this keeps the `(advisor_id, city)` pair
  single-valued in the audit log.
- **Do not rely on `expires_at` alone for compromise response.** A
  future-dated expiry is still usable until that date. `revoked_at` is
  the immediate-effect lever.

---

## 9. Incident Response

### Compromise detection signals

| Signal                                                                       | Severity  |
|------------------------------------------------------------------------------|-----------|
| Advisor reports lost device / stolen laptop                                  | High      |
| `engagement_events` shows actions outside that advisor's normal hours        | Medium    |
| Advisor's `X-Admin-Key` found in a git commit, paste, screenshot, or chat    | High      |
| Off-hours burst of `advisor_action` rows for one `advisor_id_hash`           | Medium    |
| Access attempt from an unexpected source IP (if IP logging is enabled)       | Low/Med   |
| Advisor personnel change (offboarding)                                       | High      |

### Immediate response (within 15 minutes of detection)

1. **Revoke the token** (see Section 8). This is the primary lever.
2. **Record the incident timestamp, advisor_id, and detection signal**
   in the infra change log.
3. **Query recent advisor actions** for that advisor:
   ```sql
   SELECT created_at, payload_json
     FROM engagement_events
    WHERE category = 'advisor_action'
      AND json_extract(payload_json, '$.advisor_id_hash') = '<hash>'
      AND created_at >= datetime('now', '-7 days')
    ORDER BY created_at DESC;
   ```
4. **Flag any cross-city or off-hours hits** for manual review. These
   are the most likely abuse signatures.

### Post-incident cleanup (within 24 hours)

- Issue a fresh token to the advisor if access is still required.
- File a post-incident note in `docs/ops/` (or the infra change log)
  covering: detection signal, time-to-revoke, scope of actions
  performed with the compromised token, data that may have been
  exfiltrated, remediation steps taken.
- If the token was exposed via a controllable channel (git, paste bin,
  chat), ensure the secret-scanning pre-commit hook would have caught
  it. If it would not, add a detection rule for the `mw_adv_` prefix.
- Review whether additional controls are warranted: IP allow-listing on
  the advisor endpoints, shorter default `expires_at`, additional audit
  hooks.

### What the prefix `mw_adv_` buys us

A single `grep -r "mw_adv_"` across the codebase, chat archives, and
log stores is an effective leak-hunting tool. Secret scanners (e.g.
gitleaks, trufflehog) take a regex rule
(`mw_adv_[A-HJ-NP-Za-km-z1-9]{32}`) and surface any accidental paste
immediately.

---

## 10. Backend Enforcement Contract

Every advisor-scoped endpoint in T12.31 (and any future advisor
endpoint) **must** comply with the following contract. Violations are
review-blockers.

### C1 — Dependency returns `(advisor_id, city)`

```python
async def require_advisor_token(
    x_admin_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> tuple[str, str]:
    """Validate the header, return (advisor_id, city). Raise uniform 401."""
```

Contract points:

- Raises **HTTP 401** with a uniform `{"detail": "Invalid advisor token"}`
  body on any failure — missing row, revoked row, expired row, or
  constant-time-compare miss. No enumeration oracle.
- Uses `hmac.compare_digest` for the hash compare (constant-time).
- The FastAPI `Header(...)` declaration means missing-header returns
  422 automatically (framework default) — this is acceptable because
  422 vs 401 on a missing header is not an enumeration oracle.

### C2 — Every query is filtered by `city = advisor.city`

The filter lives in the **repository layer**, not just the route
handler. A route handler that accepts `(advisor_id, city)` but forgets
to thread `city` into the repository call must be rejected at review.

```python
# CORRECT
sessions = await sessions_repo.list_stalled_for_city(db, city=city)

# INCORRECT — city filter missing; relies on route-layer discipline
sessions = await sessions_repo.list_stalled(db)
filtered = [s for s in sessions if s.city == city]  # bad
```

### C3 — Cross-city access returns HTTP 403, never 404, never empty

When an advisor for `montgomery` requests a session whose
resolved city is `prince-georges`:

```python
if session.city != advisor_city:
    raise HTTPException(
        status_code=403,
        detail="Cross-city access denied",
    )
```

- **Not 404** — 404 hides the policy violation from the audit log.
- **Not an empty list / null body** — silent failures look like bugs,
  never escalate.

### C4 — Every advisor action writes to `engagement_events`

```python
await engagement_events.insert(
    db,
    category="advisor_action",
    payload={
        "advisor_id_hash": sha256(advisor_id).hexdigest(),
        "action": "view_stalled_session",  # or send_reminder_note, etc.
        "session_id": session_id,
        "city": city,
        "timestamp": now_iso(),
    },
)
```

- `advisor_id` is **hashed** before write (mirrors
  `hash_actor_token` in `app.core.feature_flags` / T12.0b).
- Reviewers correlate hash → identity through a short-lived DB query,
  never from the log alone.
- The `city` field on the event makes per-city audit queries trivial.

### C5 — Uniform 401 on all auth failures (no enumeration oracle)

Response body on every auth failure is byte-identical:
`{"detail": "Invalid advisor token"}`. No hints about which specific
check failed. Existing precedent: T12.10b manage-link token verification.

### C6 — Rate limit per actor hash

Reuse `_check_rate_limit(actor_hash, scope='advisor', max_per_hour=60)`
from `app.core.feature_flags`. Advisor inbox traffic is human-scale; 60
requests/hour is generous for normal use and anomalous for abuse.
Exceeding raises HTTP 429.

---

## 11. Schema Gap — `sessions` has no `city` column

`backend/app/core/migrations/m001_initial.py` does not give `sessions`
a `city` column. Today, city is inferred from
`outcomes_records.payload_json.city` (per S12a T12.25 notes). For the
advisor inbox:

- The "is this session in my city?" check requires a join to
  `outcomes_records` with a JSON-path extraction on `payload_json.city`.
- Sessions without an outcomes record (worker abandoned before
  feedback) have no resolvable city and MUST be excluded from advisor
  views — not shown, not surfaced as an error.

**Recommendation:** add `sessions.city TEXT` via a new migration
(`m00X_sessions_city.py`) in S12b or S13, backfill from outcomes. Until
then, T12.31 endpoints use the join pattern and document it inline.

---

## 12. Threat Model Addressed

| Threat                                  | Mitigation                                                                      |
|-----------------------------------------|---------------------------------------------------------------------------------|
| Cross-city PII leak                     | Mandatory `city = advisor.city` filter at repo layer + 403 on mismatch          |
| Token theft                             | 6-month rotation, immediate `revoked_at`, per-token audit granularity           |
| Insider abuse                           | Per-advisor audit trail; periodic review of off-hours / volume anomalies        |
| Secret leakage to git / paste           | `mw_adv_` prefix enables secret-scanner rules and leak-hunt greps               |
| Replay / enumeration                    | Uniform 401 body on every auth failure; no per-failure-mode response variance   |
| Privilege escalation via header sharing | Mechanical review: admin and advisor routes use disjoint dependencies           |

---

## 13. Not Addressed (Deferred)

- Fine-grained per-session permissions (advisors have all-or-nothing
  access within their city).
- Multi-city tokens (one advisor, multiple cities) — would require a
  `cities TEXT[]` column and per-row ACL; out of scope for S12b.
- SSO / federated identity (no IdP integration).
- Self-service advisor token rotation — all rotations are operator-run
  through the CLI or SQL fallback.
- IP allow-listing on advisor endpoints — considered for S13 if
  compromise incidents warrant it.

---

## 14. Implementation Notes for T12.31

### Expected file layout

| File                                                     | Responsibility                                                     |
|----------------------------------------------------------|--------------------------------------------------------------------|
| `backend/app/core/migrations/m00X_advisor_tokens.py`     | New migration — creates `advisor_tokens` table                     |
| `backend/app/modules/advisor/tokens.py`                  | `hash_token`, `validate_token`, `revoke_token` helpers             |
| `backend/app/modules/advisor/auth.py`                    | `require_advisor_token` FastAPI dependency                         |
| `backend/app/modules/advisor/repository.py`              | City-filtered queries (stalled sessions, outcome detail)           |
| `backend/app/routes/case_manager.py`                     | `/api/case-manager/*` route handlers using the dependency          |
| `backend/tests/test_advisor_auth.py`                     | Dependency-level tests (valid, revoked, wrong-city 403, etc.)      |
| `backend/tests/test_advisor_repository.py`               | Repository-level tests (city filter enforced, no cross-city leak)  |
| `backend/tests/test_case_manager_routes.py`              | End-to-end route tests                                             |

### Expected signatures

```python
# backend/app/modules/advisor/auth.py
async def require_advisor_token(
    x_admin_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> tuple[str, str]:
    """Validate token, return (advisor_id, city). Uniform 401 on failure."""

# backend/app/modules/advisor/tokens.py
def hash_token(plaintext: str) -> str: ...

async def validate_token(
    db: AsyncSession, plaintext: str,
) -> tuple[str, str] | None:
    """Return (advisor_id, city) or None. None is ALL failure modes."""

async def revoke_token(
    db: AsyncSession, advisor_id: str,
) -> int:
    """Mark all active rows for advisor_id as revoked. Return count."""

# backend/app/modules/advisor/repository.py
async def list_stalled_sessions_for_city(
    db: AsyncSession, city: str, limit: int = 50,
) -> list[StalledSession]: ...

async def get_session_detail_for_city(
    db: AsyncSession, session_id: str, city: str,
) -> SessionDetail:
    """Raise HTTPException(403) if resolved city != advisor city."""
```

### Expected migration shape

```sql
CREATE TABLE advisor_tokens (
    token_hash  TEXT PRIMARY KEY,
    advisor_id  TEXT NOT NULL,
    city        TEXT NOT NULL,
    issued_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at  TIMESTAMP,
    expires_at  TIMESTAMP
);

CREATE INDEX idx_advisor_tokens_advisor_id ON advisor_tokens(advisor_id);
CREATE INDEX idx_advisor_tokens_active
    ON advisor_tokens(advisor_id, city)
 WHERE revoked_at IS NULL;
```

### Implementation checklist (for the T12.31 driver)

- [ ] New `advisor_tokens(token_hash, advisor_id, city, issued_at,
      revoked_at, expires_at)` migration
- [ ] Optional: `sessions.city` column + backfill migration (cleaner
      scope enforcement)
- [ ] `require_advisor_token` FastAPI dependency returning
      `(advisor_id, city)`; uniform 401 on all failure modes
- [ ] Per-query `city = advisor.city` filter baked into every
      advisor-facing repository method (**not** just route handler)
- [ ] HTTP 403 on cross-city session access (never 404, never empty)
- [ ] Audit-log insert into
      `engagement_events(category='advisor_action', ...)` on every
      advisor action
- [ ] SHA256 hashing of `advisor_id` before audit-log write
- [ ] Rate limit via `_check_rate_limit(actor_hash, scope='advisor',
      max_per_hour=60)`
- [ ] CLI token issuance command (`bpsai-pair advisor issue`) OR
      documented manual SQL procedure for S12b
- [ ] Revocation path documented and exercised in an end-to-end test
- [ ] `mw_adv_` prefix secret-scanner rule added to pre-commit config
- [ ] Reviewed by security lead (tracked via PR review requirement —
      out-of-band process)

---

## 15. Cross-References

- `docs/ops/appointment-token-rotation.md` — HMAC signing-key rotation
  runbook; parallel structure for a different token class.
- `backend/app/core/auth.py` — existing `require_admin_key` dependency
  that this model extends.
- `backend/app/modules/appointments/tokens.py` — HMAC-signed token
  reference (T12.10b); the pattern we explicitly chose **not** to reuse
  for advisor auth, and the rationale (Section 5).
- `backend/app/modules/engagement/unsubscribe_tokens.py` — a second
  HMAC-signed token reference (T12.21).
- `backend/app/routes/admin_flags.py` — rate-limit precedent
  (`_check_rate_limit`, `hash_actor_token`) that advisor auth reuses.
