# T13.98 — CSRF Audit

**Sprint:** S13
**Method:** Audit auth model; classify CSRF surface; verify state-changing routes have appropriate protection.
**Generated:** 2026-04-25

## Auth model summary

MontGoWork's worker auth uses **token-in-body** (not cookies):

- Worker session is identified by `session_id` (UUID, in body) + `session_token` (random 96-bit, in body)
- The token is delivered via a signed feedback link (e.g., `/feedback/{token}` for first arrival)
- Subsequent requests carry both fields in the JSON body of every state-changing call

This design is **inherently CSRF-resistant**: a cross-origin attacker cannot make the user's browser include the token because:
1. The token is in the request body, not in cookies
2. There's no `withCredentials: true` cookie-based session
3. CORS prevents cross-origin sites from reading the token from a same-origin response

**Traditional CSRF protection (synchronizer tokens, double-submit cookies) is unnecessary for this auth model.**

## Other auth contexts

| Context | Auth | CSRF surface | Protection |
|---------|------|-------------|------------|
| Worker session | session_id + token in body | None | Token-in-body design |
| Feedback link (first-touch) | random token in URL query | One-shot URL; no further state mutation possible without escalating to session_token | Token entropy (96-bit) |
| Manage-appointment link | signed token in URL query (HMAC + kid + single-use) | URL is the credential; clicking is the action | Single-use enforcement (T13.61); uniform 401 on misuse |
| Unsubscribe link | signed token in URL query | CAN-SPAM idempotent (T13.61); GET + POST both valid | Token signature + idempotent design |
| Admin endpoints | `X-Admin-Key` header (`hmac.compare_digest`) | Header-based; cookies not in play | Same as session — header-based, not cookie-based |
| Advisor session | DB-row token (advisor_tokens m007) | Header-based (per T12.31a auth doc) | Same |

## Findings

**Zero CSRF findings for the worker-facing surface.**

### Verified clean

- No cookie-based session anywhere in `backend/app/`. Searched for `set_cookie`, `Cookie`, `Set-Cookie` headers being set — zero matches.
- FastAPI's response models don't set cookies on any state-changing route.
- The frontend does NOT use `withCredentials` on cross-origin fetches.
- CORS is configured with explicit `CORS_ORIGINS` env var (locked in by T13.118 startup validator).

### Edge cases worth flagging (not findings)

1. **Manage-appointment GET pre-fetch.** Email clients (Outlook, Gmail) prefetch links on hover/preview. This means the user's browser may "click" the cancel link without intent. **Mitigations already in place:**
   - The cancel route is GET-with-side-effect (typically a CSRF concern); single-use enforcement (T13.61) means a prefetch consumes the token. If the user then clicks intentionally, the request lands on a now-invalid token and gets a uniform 401.
   - This is a UX concern (user clicks "cancel" on an email after Outlook prefetched it; sees 401), not a security one. The cancellation IS what the email author intended.

2. **Unsubscribe GET prefetch.** Same situation. T13.61's CAN-SPAM idempotency fix means prefetch-then-click both succeed and only one opt-out row exists. **Behavior is correct by design.**

3. **Share-link prefetch.** The share endpoint is read-only — no state mutation; no CSRF surface. (Separate P0 finding from T13.71 about content disclosure, not CSRF.)

## Recommendation

- No CSRF code changes required.
- **Optional hardening (P2, S14+):** add `Content-Security-Policy: frame-ancestors 'none'` and `X-Frame-Options: DENY` headers to prevent clickjacking. Not technically CSRF, but adjacent threat model.
- **Document the auth model in `docs/architecture.md`** so future contributors don't mistakenly add cookie-based session logic that would introduce CSRF surface.

## Out of scope

- Login-form CSRF (no traditional login form exists; first-touch is the feedback URL)
- Cross-site script include CSRF (no JSONP endpoints)
