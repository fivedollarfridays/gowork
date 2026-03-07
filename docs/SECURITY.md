# Security

> Security posture overview for MontGoWork. Covers fixed findings, accepted risks, and architecture decisions from the Sprint 18 hardening effort (GitHub Issue #20).

## Security Architecture

### Authentication

- **BrightData admin endpoints** (`/api/brightdata/*`) require `X-Admin-Key` header validated against `ADMIN_API_KEY` env var. Returns 503 if not configured, 403 on mismatch.
- **User-facing endpoints** are unauthenticated by design (public kiosk model).

### Input Validation

- All `session_id` path parameters enforce UUID regex (`^[0-9a-f]{8}-...`).
- `snapshot_id` path parameters enforce alphanumeric regex with 200-char max.
- Pydantic models validate request body fields (types, ranges, patterns).
- Free-text fields (`qualifications`, `free_text`) enforce `max_length` limits.

### Rate Limiting

- `POST /api/assessment/` — 10 req/min per IP
- `POST /api/plan/{id}/generate` — 5 req/min per IP
- `POST /api/credit/assess` — 10 req/min per IP
- `POST /api/feedback/*` — 20 req/min per IP
- Implementation: in-memory per-process `RateLimiter` in `app/core/rate_limit.py`.

### AI/LLM Defense

- System prompt includes untrusted-data handling instructions.
- User-supplied text (barriers, qualifications) wrapped in `<user_input>` XML tags to prevent prompt injection.

### Security Headers (Frontend)

Configured in `next.config.mjs`:
- `X-Frame-Options: DENY`
- `Content-Security-Policy` (script-src self, style-src self unsafe-inline)
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` (camera, microphone, geolocation disabled)

### CORS

- Methods restricted to `GET`, `POST`, `OPTIONS`.
- Headers restricted to `Content-Type`, `X-Admin-Key`.

### Container Hardening

- Both Dockerfiles run as non-root `appuser`.
- No hardcoded env overrides in `docker-compose.yml`.

## Fixed Findings

| ID | Finding | Resolution |
|----|---------|------------|
| SEC-001 | BrightData endpoints unauthenticated | `require_admin_key` dependency on all 3 endpoints (T18.1) |
| SEC-002 | Weak token generation | Already fixed — SHA256 + base64url, 12-char tokens |
| SEC-003 | No prompt injection defense | System prompt instruction + XML tag wrapping (T18.2) |
| SEC-008 | Missing security headers | 5 headers added to next.config.mjs (T18.3) |
| SEC-009 | Containers run as root | Non-root `appuser` in both Dockerfiles (T18.4) |
| SEC-010 | No rate limiting on expensive endpoints | Rate limiters on 4 endpoint groups (T18.6) |
| SEC-011 | No max_length on free_text | Already fixed — `max_length=2000` on Pydantic field |
| SEC-012 | No session_id validation | UUID regex on all path params + Pydantic fields (T18.5) |
| SEC-013 | Permissive CORS | Methods + headers restricted (T18.3) |
| SEC-016 | Raw error content logged | Logger logs length, not raw response body (T18.5) |
| SEC-017 | Session ID leaked in validate response | Removed from response body (T18.5) |
| SEC-018 | Docker env overrides | Removed hardcoded values from docker-compose.yml (T18.4) |
| SEC-020 | No CI vulnerability scanning | pip-audit + npm audit added to CI (T18.7) |
| SEC-023 | No snapshot_id validation | Alphanumeric regex + max_length on path param (T18.5) |
| SEC-026 | No session expiry | Already fixed — 24-hour TTL with `expires_at` column |

## Accepted Risks

| ID | Finding | Risk Level | Rationale |
|----|---------|------------|-----------|
| SEC-006 | Rate limiter is per-process (in-memory) | Low | Single-worker deployment. Acceptable for kiosk demo. Would need Redis/shared store for multi-worker horizontal scaling. |
| SEC-007 | Credit proxy surfaces upstream errors | Low | Error codes (503/504/502) are passed through by design. No sensitive data in error responses — upstream body is not forwarded. |
| SEC-014 | EmailJS sends PII client-side | Low | EmailJS is a client-side email service. Plan data is user-initiated export. No server-side PII storage beyond session TTL. |
| SEC-015 | QR feedback token in PDF | Low | Tokens are short-lived (30-day expiry), non-sequential (SHA256), and link to anonymous feedback form only. By design for print-and-visit workflow. |
| SEC-019 | DATA_DIR path hardcoded | Low | `DATA_DIR` defaults to `./data` relative to working directory. Configurable via env var. SQLite file location is an operational concern, not a security vulnerability. |

## CI Scanning

### Backend (`pip-audit`)

Runs `pip-audit -r requirements.txt` in the CI backend job. Fails the build on any known vulnerability in Python dependencies.

### Frontend (`npm audit`)

Runs `npm audit --audit-level=high` in the CI frontend job. Fails on high or critical severity vulnerabilities only. Moderate/low findings are reviewed manually during dependency updates.

### Secret Scanning

Existing CI job (`security`) scans for hardcoded secrets in source files and verifies no `.env` files are committed.
