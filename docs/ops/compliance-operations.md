# Compliance Operations Runbook (T12.36)

**Scope**: worker-initiated data export, full account deletion, selective
category deletion, retention sweep. This document is the authoritative
reference for advisors, legal, and ops when a worker exercises a
compliance right.

---

## 1. Worker data request workflow

### Export (the worker wants a copy of their data)

**API**: `POST /api/compliance/export`
**Auth**: worker's `feedback_tokens` row (session-scoped).
**Rate limit**: 3 requests/hour/session (HTTP 429 when exceeded).

Request body:

```json
{
  "session_id": "sess-xxx",
  "session_token": "worker-feedback-token"
}
```

Response body (200):

```json
{
  "archive_id": "20260423T120000Z",
  "download_url": "/api/compliance/export/download?token=<signed>",
  "expires_in_sec": 86400
}
```

The `download_url` is:

* **Signed** with `COMPLIANCE_TOKEN_SECRET` (HMAC-SHA256, `kid` +
  rotation, same pattern as T12.10b manage-appointment tokens).
* **Single-use** — second `GET` on the same URL returns HTTP 401
  (atomic enforcement via the `used_tokens` table; UNIQUE constraint
  makes concurrent replay impossible).
* **24-hour TTL** — after 24 hours the token is rejected.

Advisors can front this flow by emailing the worker the `download_url`
themselves (no code change needed — existing dispatch can carry the URL
as a bare string).

### Full delete (the worker wants their account erased)

**API**: `POST /api/compliance/delete`

Request body:

```json
{
  "session_id": "sess-xxx",
  "session_token": "worker-feedback-token",
  "confirm": "DELETE",
  "reason": "worker request — in person"
}
```

The `confirm` field is a client-side speed bump; the server rejects
missing / wrong values with HTTP 400. Behaviour on success:

1. Writes `compliance_audit` row with `action="full_delete"` and a
   SHA256-hashed `session_id` (the raw id is NOT stored on the audit
   row — it would outlive the session otherwise).
2. Issues `DELETE FROM sessions WHERE id = ?` with foreign keys
   enforced. Every S12 child table is cleared by the `ON DELETE CASCADE`
   chain from m002.
3. Explicitly clears `record_profiles` (m001 predates the CASCADE
   contract — no FK on its `session_id`).

**This is irreversible.** There is no undelete path.

### Selective delete (the worker wants to purge a specific category)

**API**: `POST /api/compliance/delete/selective`

Request body:

```json
{
  "session_id": "sess-xxx",
  "session_token": "worker-feedback-token",
  "category": "criminal_record",
  "reason": "worker opted out of fair-chance lane"
}
```

Behaviour on success:

1. Sets `deleted_at` / `deleted_reason` on the rows tied to that
   category (tombstone — rows physically remain).
2. All reads must filter `WHERE deleted_at IS NULL`. The canonical
   tombstone-aware reader is `compliance.delete.read_record_profile`.
3. Writes `compliance_audit` row with `action="selective_delete"`.

**Currently in scope**: `criminal_record` → `record_profiles`.
**Tables with tombstone columns**: `record_profiles`, `resume_versions`,
`engagement_events` (future categories can extend `CATEGORY_TO_TABLE`
in `delete.py` without a new migration).

---

## 2. Advisor role

Advisors (not workers) may initiate compliance actions on behalf of a
worker during case-management conversations:

* Confirm the worker's identity in person / on a verified channel.
* Obtain explicit consent (ideally signed); record the exact wording
  in the `reason` field.
* Record the advisor's name in the `reason` field — the server hashes
  the session token into `actor_token_hash`, so the free-text reason
  is the human audit trail.
* For the export flow, forward the `download_url` only to the
  worker's verified email. Never share it on a public channel; the
  token is single-use but the 24-hour TTL gives a stolen link time to
  be used.

Advisor-initiated deletes should be rare — prefer worker-initiated
deletes when possible so the worker's token proves consent.

---

## 3. Legal escalation path

Escalate to legal (priority 1, same-day) when any of the following
fire:

* A regulator, subpoena, or court order requests worker data.
* A worker disputes a deletion they did not initiate (check
  `compliance_audit` for the `actor_token_hash` — if it isn't theirs,
  we have a security incident).
* A retention purge has already deleted the session being requested.
  Audit rows persist but the underlying PII does not — be honest
  about what we can and cannot produce.
* Any export / delete that cannot be satisfied within 30 days
  (regulatory SLA).

Legal contact: [team slack / email alias redacted at repo level —
populate per deployment].

---

## 4. Retention sweep

Runs nightly as the final step of `scripts.nightly_digest`. Purges
sessions where `expires_at + 90 days` is past. The 90-day grace window
is defined in `compliance.retention.RETENTION_GRACE_DAYS`.

Per purge:

* Audit row (`action="retention_purge"`) written BEFORE the delete.
* `DELETE FROM sessions` with FK enforcement; children cascade out.
* Errors on any single session are logged and skipped; they never
  abort the batch (matches the T12.24/T12.25a robustness contract).

To change the grace window, edit `RETENTION_GRACE_DAYS` in
`backend/app/modules/compliance/retention.py`. Any change is effective
on the next nightly run; no migration required.

### Manually running the sweep

```python
from datetime import datetime, timezone
from app.modules.compliance.retention import retention_sweep

purged = retention_sweep(
    db_path="/path/to/app.db",
    now=datetime.now(timezone.utc),
)
print(f"Purged {len(purged)} sessions")
```

---

## 5. Token secret rotation

The `COMPLIANCE_TOKEN_SECRET` environment variable holds the current
signing key. Rotation follows the same pattern as T12.10b:

1. Set `COMPLIANCE_TOKEN_SECRET_OLD` to the current secret.
2. Rotate `COMPLIANCE_TOKEN_SECRET` to the new secret.
3. Wait 24 hours (longer than the export token TTL) so all in-flight
   tokens expire naturally.
4. Unset `COMPLIANCE_TOKEN_SECRET_OLD`.

During the rotation window both secrets validate; only the new secret
signs new tokens.

---

## 6. Audit trail queries

Every compliance action writes a row to `compliance_audit`. Common
queries:

```sql
-- All actions on a session (pass the SHA256 hex of the session id)
SELECT action, category, payload_json, created_at
FROM compliance_audit
WHERE session_id_hash = ?
ORDER BY created_at DESC;

-- Full-delete rate in the last day
SELECT COUNT(*) FROM compliance_audit
WHERE action = 'full_delete'
  AND created_at > datetime('now', '-1 day');

-- Retention sweeps per week
SELECT date(created_at) as day, COUNT(*) as purges
FROM compliance_audit
WHERE action = 'retention_purge'
GROUP BY day
ORDER BY day DESC;
```

The raw `session_id` is never stored in the audit table — it is
SHA256-hashed so audit rows outlive the session without leaking the
id. Use the same hash to correlate a specific session's lifecycle.
