# Security

> Security posture overview for MontGoWork. All 26 findings from GitHub Issue #20 are resolved across Sprint 18-19. Sprint 30 security audit addressed 8 additional findings.

## Security Architecture

### Authentication

- **BrightData admin endpoints** (`/api/brightdata/*`) require `X-Admin-Key` header validated against `ADMIN_API_KEY` env var. Returns 503 if not configured, 403 on mismatch. Uses `hmac.compare_digest` for timing-safe comparison.
- **Plan and feedback endpoints** require session-scoped tokens (issued at assessment time). Tokens are validated against the owning session to prevent cross-session access.
- **User-facing endpoints** (assessment, credit) are unauthenticated by design (public kiosk model).

### Input Validation

- All `session_id` path parameters enforce UUID regex (`^[0-9a-f]{8}-...`).
- `snapshot_id` path parameters enforce alphanumeric regex with 200-char max.
- Pydantic models validate request body fields (types, ranges, patterns).
- Free-text fields (`qualifications`, `free_text`) enforce `max_length` limits.

### Rate Limiting

- Assessment: 10 req/min per IP
- Plan generate: 5 req/min per IP
- Credit assess: 10 req/min per IP
- Feedback: 20 req/min per IP
- Jobs list: 60 req/min per IP
- Jobs detail: 120 req/min per IP
- Barrier-intel chat: 10 req/min per IP
- Implementation: in-memory per-process `RateLimiter` in `app/core/rate_limit.py`.

### AI/LLM Defense

- System prompt includes untrusted-data handling instructions
- User-supplied text (barriers, qualifications) wrapped in `<user_input>` XML tags to prevent prompt injection
- Barrier intelligence chat has topic guardrails (filters disallowed topics, returns safe fallback)
- Multi-provider LLM client with graceful fallback chain (Anthropic -> OpenAI -> Gemini -> Mock)

### Backend Security Headers

Configured via `SecurityHeadersMiddleware` in `app/main.py`:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Cache-Control: no-store` on API responses
- `Permissions-Policy` (camera, microphone, geolocation disabled)

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

### Production Configuration Validators

Pydantic model validators in `core/config.py` enforce safe configuration:
- `audit_hash_salt` must be changed from default in production (warns in staging)
- `admin_api_key` must not be weak/empty in production
- `cors_origins` must not contain `localhost` in production

### PII Protection

- Criminal record `record_profile` is excluded from API responses and session storage blobs
- Audit logging uses salted SHA-256 hashed session IDs -- no user content logged
- Only metadata (prompt length, response length, provider, latency) is recorded in LLM audit logs

### Frontend Input Sanitization

- `safeHref()` utility blocks `javascript:` and `data:` URL schemes on all external links
- ZIP code regex validation (`/^\d{5}$/`) on findhelp.org URL generation
- All user-facing URLs pass through allowlist validation

### CSRF Protection

The API is fully stateless — no cookies and no server-side sessions. All client state is carried via:

- URL query parameters (`token`)
- URL path parameters (`session_id`, `snapshot_id`)
- JSON request bodies

Because no cookies are used, the browser never attaches ambient credentials to cross-origin requests, which eliminates the CSRF attack vector. CORS configuration (restricted origins, methods, and headers) provides an additional layer of defense.

**If cookie-based authentication is ever added**, CSRF tokens (e.g., `Double Submit Cookie` or `Synchronizer Token` pattern) must be implemented before deployment.

### Audit Logging

Structured JSON audit events emitted via the `audit` logger for security-relevant actions:
- `session_created` — new assessment submitted
- `plan_accessed` / `plan_generated` — plan viewed or AI narrative generated
- `credit_assessed` — credit proxy called
- `feedback_resource` / `feedback_visit` — feedback submitted

Each entry includes `event`, `session_id`, `client_ip`, and action-specific details.

### Container Hardening

- Both Dockerfiles run as non-root `appuser`.
- No hardcoded env overrides in `docker-compose.yml`.

## Resolved Findings (26/26)

All findings from GitHub Issue #20 are resolved. No accepted risks remain.

| ID | Finding | Resolution |
|----|---------|------------|
| SEC-001 | BrightData endpoints unauthenticated | `require_admin_key` dependency on all 3 endpoints (T18.1) |
| SEC-002 | Weak token generation | SHA256 + base64url, 16-char tokens with 96-bit entropy (T18.5, T19.5) |
| SEC-003 | No prompt injection defense | System prompt instruction + XML tag wrapping (T18.2) |
| SEC-004 | Plan endpoint unauthenticated | Session-scoped token required on all plan endpoints (T19.1) |
| SEC-005 | Feedback endpoint unauthenticated | Session-scoped token required on all feedback endpoints (T19.1) |
| SEC-006 | Rate limiter is per-process | ProxyHeadersMiddleware added; startup warning when `WEB_CONCURRENCY > 1`; documented in DEPLOYMENT.md (T19.2, T21.3) |
| SEC-007 | Credit proxy surfaces upstream errors | Error masking: generic messages to client, upstream details logged server-side only (T19.3) |
| SEC-008 | Missing security headers | 5 headers added to next.config.mjs (T18.3) |
| SEC-009 | Containers run as root | Non-root `appuser` in both Dockerfiles (T18.4) |
| SEC-010 | No rate limiting on expensive endpoints | Rate limiters on 4 endpoint groups (T18.6) |
| SEC-011 | No max_length on free_text | `max_length=2000` on Pydantic field (pre-existing) |
| SEC-012 | No session_id validation | UUID regex on all path params + Pydantic fields (T18.5) |
| SEC-013 | Permissive CORS | Methods + headers restricted (T18.3) |
| SEC-014 | EmailJS sends PII client-side | Replaced with link-based approach: plan URL only, no PII in email transit (T19.4) |
| SEC-015 | QR feedback token in PDF | Tokens are 30-day expiry, non-sequential (SHA256), link to anonymous feedback only (T19.1) |
| SEC-016 | No snapshot_id validation | Alphanumeric regex + max_length on path param (T18.5) |
| SEC-017 | Raw error content logged | Logger logs length, not raw response body; structured audit logging (T18.5, T19.8) |
| SEC-018 | Docker env overrides | Removed hardcoded values from docker-compose.yml (T18.4) |
| SEC-019 | DATA_DIR path hardcoded | Configurable via `DATA_DIR` env var; missing files logged as warnings (T19.6) |
| SEC-020 | No CI vulnerability scanning | pip-audit + npm audit added to CI (T18.7) |
| SEC-021 | Default API URL in Dockerfile | Removed default from Dockerfile.frontend; must be set at build time (T19.7) |
| SEC-022 | Token entropy insufficient | `secrets.token_urlsafe(12)` produces 96-bit entropy (T19.5) |
| SEC-023 | Session ID leaked in validate response | Removed from response body (T18.5) |
| SEC-024 | No encryption at rest documentation | DEPLOYMENT.md documents host-level encryption requirement (T19.9) |
| SEC-025 | No CSRF protection stance | SECURITY.md documents stateless API CSRF stance (T19.9) |
| SEC-026 | No session expiry | 24-hour TTL with `expires_at` column (pre-existing) |

### Sprint 30 Audit Findings (8/8)

| ID | Finding | Resolution |
|----|---------|------------|
| HIGH-1 | Criminal record PII in API response | `record_profile` excluded from response body and session blob |
| HIGH-2 | Default audit salt accepted in production | Pydantic validator rejects default salt in production, warns in staging |
| MED-1 | No backend security headers | `SecurityHeadersMiddleware` added to FastAPI app |
| MED-2 | Potential SSRF on external URLs | URL allowlisting on outbound API calls |
| MED-3 | Timing-attackable admin key check | Replaced `==` with `hmac.compare_digest` |
| MED-4 | LLM prompt injection surface | `<user_input>` XML wrapping on all user-supplied text |
| LOW-1 | findhelp.org URL parameter injection | ZIP code regex validation on both frontend and backend |
| LOW-2 | External link XSS via javascript: href | `safeHref()` blocks javascript: and data: URL schemes |

## CI Scanning

### Backend (`pip-audit`)

Runs `pip-audit -r requirements.txt` in the CI backend job. Fails the build on any known vulnerability in Python dependencies.

### Frontend (`npm audit`)

Runs `npm audit --audit-level=high` in the CI frontend job. Fails on high or critical severity vulnerabilities only. Moderate/low findings are reviewed manually during dependency updates.

### Secret Scanning

Existing CI job (`security`) scans for hardcoded secrets in source files and verifies no `.env` files are committed.
