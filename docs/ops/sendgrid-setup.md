# SendGrid Setup Runbook (T12.2)

Operational guide for provisioning SendGrid for MontGoWork transactional email
(digests, reminders, stall alerts, appointment confirmations / reminders).

## 1. Account + API Key

1. Sign up / sign in at <https://app.sendgrid.com>.
2. Navigate to **Settings -> API Keys -> Create API Key**.
3. Name the key `montgowork-mail-send-<env>` (e.g. `montgowork-mail-send-prod`).
4. **Key scoping (REQUIRED): "Restricted Access"** — enable ONLY the single
   permission **Mail Send -> Full Access**. Leave every other scope OFF.
   Specifically these scopes MUST remain disabled:
   - Contact lists / Marketing
   - Sender Authentication management
   - Email Activity read
   - Stats / Billing / Team / IP Management
5. Copy the key once (SendGrid only shows it on creation). Store it in the
   secret manager — never in git. Expose it to the app as
   `SENDGRID_API_KEY=<value>`. See `.env.example` for the placeholder.
6. Also set `SENDGRID_FROM_EMAIL=<verified_sender>` for the `From:` header.

## 2. Sender Domain Authentication (SPF + DKIM)

Add these DNS records to the sending domain (replace `montgowork.app` with
your real domain; SendGrid generates the `sXX._domainkey` selectors when you
run **Settings -> Sender Authentication -> Authenticate Your Domain**):

| Type  | Host                          | Value (template)                                  |
|-------|-------------------------------|---------------------------------------------------|
| TXT   | `@`                           | `v=spf1 include:sendgrid.net ~all`                |
| CNAME | `em1234.montgowork.app`       | `u12345.wl123.sendgrid.net`                       |
| CNAME | `s1._domainkey.montgowork.app` | `s1.domainkey.u12345.wl123.sendgrid.net`         |
| CNAME | `s2._domainkey.montgowork.app` | `s2.domainkey.u12345.wl123.sendgrid.net`         |

After DNS propagates (usually <30 min) click **Verify** in the SendGrid UI. A
green checkmark on all four records is required before enabling sends in
production.

## 3. Event Webhook (deferred to T12.2a)

T12.2a will land the ingest endpoint. For now, pre-configure:

- **POST** URL: `https://<api-host>/api/webhooks/sendgrid/events`
- Events to ship: `delivered`, `bounce`, `dropped`, `deferred`, `spamreport`
- Signed event webhook: **enable**, store the verification key as
  `SENDGRID_WEBHOOK_VERIFICATION_KEY`

## 4. Key Rotation

1. Create a new key with the same "Mail Send" scope.
2. Roll `SENDGRID_API_KEY` in the secret manager; restart the app.
3. Verify a test digest sends successfully
   (`FEATURE_EMAIL_SEND_ENABLED=true`).
4. Revoke the old key in the SendGrid UI.
5. Record the rotation date in the ops log.

## 5. Kill Switch

Emergency stop is the `FEATURE_EMAIL_SEND_ENABLED` feature flag (T12.0b). Flip
to `false` via env var or `POST /api/admin/flags/EMAIL_SEND_ENABLED` — all
`send_transactional()` calls will return `skipped_reason="kill_switch"` and
emit an INFO log line with no SendGrid API hit.
