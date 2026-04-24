# Appointment Manage-Link Token Rotation (T12.10b)

Operational runbook for rotating `APPOINTMENT_TOKEN_SECRET`, the HMAC-SHA256
secret used to sign single-use manage-appointment links embedded in worker
emails. Tokens have a 7-day TTL by default.

## 1. Why rotate

- **Periodic hygiene**: rotate quarterly as a matter of policy, same as any
  long-lived signing key.
- **Compromise / suspected leak**: any uncontrolled exposure of the secret
  (committed to git, shared via chat, etc.) requires immediate rotation.
- **Staff offboarding**: rotate whenever a person with production-secret
  access leaves the team.

## 2. Planned rotation (no active incident)

This is the **dual-secret validation-window** procedure. Outstanding tokens
continue to verify under the old secret until they expire naturally, so no
worker sees a dead manage-link.

1. Generate a fresh secret:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
2. In the secret manager, set `APPOINTMENT_TOKEN_SECRET_OLD` to the current
   value of `APPOINTMENT_TOKEN_SECRET`.
3. Set `APPOINTMENT_TOKEN_SECRET` to the new value.
4. Restart / redeploy backend pods so both env vars are picked up at boot.
5. **Wait at least 7 days** (= the default token TTL). Every outstanding
   token signed under the old secret will expire during this window. Do
   not skip the wait — cutting it short will strand any email already in
   a worker's inbox.
6. After the 7-day window, unset `APPOINTMENT_TOKEN_SECRET_OLD` in the
   secret manager and redeploy to complete the rotation.

### Verifying the rotation

Right after step 4 and again after step 6, run:

```bash
# Should report both on first check, only `current` after cleanup.
env | grep APPOINTMENT_TOKEN_SECRET
```

Exercise a manage-link end-to-end (send yourself a test cancellation email
and click through). Expected: 200 OK and the appointment flips to
`cancelled`.

## 3. Incident rotation (secret leak)

When you have evidence the secret was exposed, the 7-day validation window
is a risk, not a feature: every outstanding token minted with the old
secret is a potential forgery vector.

1. Generate a fresh secret.
2. Set `APPOINTMENT_TOKEN_SECRET` to the new value. **Do NOT set
   `APPOINTMENT_TOKEN_SECRET_OLD`** — leaving it unset invalidates every
   outstanding token immediately.
3. Redeploy.
4. Re-send confirmation emails for any open appointments so workers have
   fresh, valid manage-links. Query outstanding scheduled appointments:
   ```bash
   sqlite3 montgowork.db \
       "SELECT id, session_id FROM appointments WHERE status='scheduled'"
   ```
   Trigger the email module's `appointment.created` re-send for each.
5. File a post-incident note documenting the root cause and adding any
   missing controls (secret-scanning pre-commit hook, audit-log alert,
   etc.).

### Note on `used_tokens`

`DELETE FROM used_tokens` only removes the replay-protection history for
already-consumed tokens; it does **not** invalidate outstanding tokens.
Never reach for it as an "invalidation" lever — changing the secret is
the only correct invalidation.

## 4. Observability

Rotations should be audited. At minimum record in the infra change log:

- Timestamp of rotation start (step 3 above).
- Operator identity.
- Reason (planned / incident).
- Timestamp of `APPOINTMENT_TOKEN_SECRET_OLD` cleanup (step 6).

Backend logs include `manage-token rejected` at DEBUG level for every
verify failure; during the validation window this count should be near
zero (all tokens should validate against either secret). A sudden spike
indicates the rotation was botched and workers are getting dead links.

## 5. Quick reference

| Scenario              | `APPOINTMENT_TOKEN_SECRET` | `APPOINTMENT_TOKEN_SECRET_OLD` |
|-----------------------|----------------------------|--------------------------------|
| Normal operation      | set                        | unset                          |
| Mid-rotation (day 0-7)| new                        | old                            |
| Rotation complete     | new                        | unset                          |
| Incident cutover      | new                        | unset                          |
