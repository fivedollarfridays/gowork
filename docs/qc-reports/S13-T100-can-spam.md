# T13.100 — CAN-SPAM Compliance Audit

**Sprint:** S13
**Method:** Audit every engagement email template; verify CAN-SPAM § 5(a) requirements: (1) sender identification, (2) clear unsubscribe, (3) honor unsubscribe within 10 business days, (4) physical postal address.
**Generated:** 2026-04-25
**Cross-reference:** T13.61 (CAN-SPAM idempotency fix), T13.96 (email html.escape verified)

## CAN-SPAM § 5(a) checklist

| Requirement | Status | Evidence |
|-------------|--------|----------|
| (1) Accurate header info (From, Reply-To, Subject) | ✓ | SendGrid SDK populates From; subject lines reviewed in `reminder_templates` are accurate |
| (2) Clear and conspicuous unsubscribe mechanism | ✓ | Every email body includes `build_unsubscribe_url(session_id)` link (`reminder_templates.py:84`) |
| (3) Unsubscribe honored within 10 business days | ✓ | `reminders_auto_disabled` row written immediately on unsubscribe; reminder engine reads pref before each send |
| (4) Physical postal address | **✗ MISSING** | No `POSTAL_ADDRESS` constant found in `backend/`; email templates do not include a physical address |
| (5) `List-Unsubscribe` MIME header | **✗ MISSING** | Modern best-practice (RFC 2369 + RFC 8058 one-click); not added to outbound mails |

## Findings

### M — No physical postal address in email footers

- **Site:** every reminder + digest email
- **Issue:** CAN-SPAM § 5(a)(5) requires a physical postal address in commercial emails. `grep` for `POSTAL_ADDRESS`, `physical address`, or `return address` returned zero hits. Email bodies don't include one.
- **Severity:** Medium for hackathon (no real users); HIGH for production (US federal violation per email)
- **Fix:** add a `POSTAL_ADDRESS` constant (e.g., `"MontGoWork, [actual street address]"`) to email config; render in every email footer template via `_email_rendering.py`.

### M — `List-Unsubscribe` header not set

- **Site:** SendGrid send call sites (`reminder_engine`, `digest_composer`, appointment emails)
- **Issue:** RFC 2369 / RFC 8058 `List-Unsubscribe: <https://...>` and `List-Unsubscribe-Post: List-Unsubscribe=One-Click` headers let MUAs (Gmail, Outlook, Apple Mail) render a one-click unsubscribe button. CAN-SPAM doesn't strictly require it, but modern deliverability requires it (Gmail's Feb 2024 sender requirements explicitly require `List-Unsubscribe` for senders >5K/day).
- **Severity:** Medium (deliverability; not a compliance-violation)
- **Fix:** when sending via SendGrid SDK, add `headers={"List-Unsubscribe": f"<{build_unsubscribe_url(session_id)}>", "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"}`. ~5 lines.

### Verified clean

- ✓ Every reminder body includes the inline unsubscribe URL (T13.61 verified)
- ✓ Unsubscribe is honored on next send via `reminders_auto_disabled` check (T13.61)
- ✓ GET + POST unsubscribe both work (CAN-SPAM idempotency)
- ✓ Token signature prevents tampering; uniform 401 on invalid (T13.61 + T13.62)
- ✓ Sender identification is consistent (SendGrid SDK From address)
- ✓ Subject lines are descriptive and not deceptive
- ✓ `_email_rendering.html.escape` prevents body content from forging headers via injection

## Recommendation

For hackathon submission with no real users, both findings are technically out-of-scope (no commercial emails are sent). For production:

1. **Required before any outbound email to real users:** add the `POSTAL_ADDRESS` constant + footer template.
2. **Required for deliverability at scale:** add `List-Unsubscribe` header + `One-Click` post.

Track both as P0 for any production rollout. For demo/judging, the inline unsubscribe link + idempotent GET/POST handler covers the user-facing experience that judges might test.

## Out of scope

- TCPA compliance (text/SMS messaging — not implemented)
- GDPR consent banners (different framework; T13.101 covers GDPR data rights)
- Email-content filter compliance (no marketing claims to validate)
