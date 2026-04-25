# Staging Deploy Runbook

**Owner:** Platform / QC
**Sprint:** S13 (T13.128)
**Status:** Drafted but not yet exercised — first deploy gates this runbook.

This runbook covers provisioning, deploying, smoke-testing, DNS, and
rollback for the MontGoWork staging environment. Production uses the
same pattern but with a different app slug, separate secrets, and
the production CORS / admin key.

---

## 1. Why Fly.io

We chose **Fly.io** for staging because:

1. **SQLite-friendly.** Fly Volumes give us a persistent disk for the
   SQLite file without standing up managed Postgres. The current app is
   intentionally single-node (`enforce_single_worker()` in
   `backend/app/main.py`), which matches Fly's single-volume-per-machine
   model.
2. **No managed-DB ceremony.** S13 is one week; bringing up RDS / Cloud
   SQL just for a staging smoke target would burn the budget.
3. **Single-binary deploy of both apps.** `fly deploy` from each
   `fly.*.toml` is two commands total.
4. **Built-in HTTPS + DNS.** Fly issues TLS certs automatically; we
   only need to add a CNAME.

> **Constraint:** SQLite + Fly Volume **does not horizontally scale**.
> If we ever need >1 backend machine, migrate to Postgres first
> (see `docs/architecture.md`). The `[[mounts]]` block in
> `deploy/fly/fly.backend.toml` is intentionally pinned to one volume.

The artifacts in this repo:

| File | Purpose |
|------|---------|
| `deploy/fly/fly.backend.toml` | Backend Fly app config (FastAPI + SQLite volume) |
| `deploy/fly/fly.frontend.toml` | Frontend Fly app config (Next.js) |
| `Dockerfile` | Backend image (already exists, unchanged) |
| `Dockerfile.frontend` | Frontend image (already exists, unchanged) |
| `scripts/staging-smoke.sh` | Post-deploy smoke check |
| `.paircoder/qc/config.yaml` `staging` profile | QC runner target |

---

## 2. Pre-Flight Checklist (One Time)

### 2.1 CLI tools

Install on your workstation:

```bash
brew install flyctl       # macOS
# OR
curl -L https://fly.io/install.sh | sh
```

Verify:

```bash
flyctl version
```

### 2.2 Fly.io account

1. Sign up at <https://fly.io/app/sign-up>.
2. Add a payment method (free tier covers staging, but Fly requires a
   card on file before launch).
3. Authenticate locally:

   ```bash
   fly auth login
   ```

### 2.3 Required secrets — gather before launch

You'll set these via `fly secrets set` in §3.4. Sources:

| Env var | Where to get the value |
|---------|------------------------|
| `ADMIN_API_KEY` | Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"` (>= 32 chars) |
| `AUDIT_HASH_SALT` | Generate: `python -c "import secrets; print(secrets.token_urlsafe(24))"` |
| `ANTHROPIC_API_KEY` | Anthropic Console → API Keys (or skip — falls back to mock) |
| `OPENAI_API_KEY` | OpenAI Platform → API Keys (optional) |
| `BRIGHTDATA_API_KEY` | BrightData dashboard (optional — staging can run without live job crawl) |
| `BRIGHTDATA_DATASET_ID` | BrightData dashboard (optional) |
| `SENDGRID_API_KEY` | SendGrid Console (optional — appointment emails) |
| `CREDIT_API_KEY` | Credit microservice owner (optional) |
| `CORS_ORIGINS` | Set after frontend app is launched. Will be `https://montgowork-staging-web.fly.dev` (or your custom CNAME). |

Do **not** commit any of these. The `.gitignore` already excludes
`backend/.env`.

> **Where the values "live" long-term:** record them in your team's
> password manager under "MontGoWork — Staging". Fly's `fly secrets
> list` will show key names but not values.

---

## 3. First-Time Deploy

> Run all commands from the **project root**:
> `/Users/<you>/Projects/montgowork`.

### 3.1 Launch backend app (no deploy yet)

```bash
fly launch \
    --copy-config \
    --config deploy/fly/fly.backend.toml \
    --name montgowork-staging-api \
    --region iad \
    --no-deploy
```

`fly launch` will detect the `Dockerfile` reference, copy the toml in
place under the working directory, and create the Fly app shell.

### 3.2 Create the SQLite volume

```bash
fly volumes create montgowork_staging_db \
    --app montgowork-staging-api \
    --region iad \
    --size 1   # GB; cheapest option, plenty for staging
```

Confirm:

```bash
fly volumes list --app montgowork-staging-api
```

### 3.3 Launch frontend app (no deploy yet)

```bash
fly launch \
    --copy-config \
    --config deploy/fly/fly.frontend.toml \
    --name montgowork-staging-web \
    --region iad \
    --no-deploy
```

### 3.4 Set backend secrets

```bash
fly secrets set --app montgowork-staging-api \
    ADMIN_API_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(32))')" \
    AUDIT_HASH_SALT="$(python -c 'import secrets;print(secrets.token_urlsafe(24))')" \
    CORS_ORIGINS="https://montgowork-staging-web.fly.dev"
# Optional — add any you have:
fly secrets set --app montgowork-staging-api \
    ANTHROPIC_API_KEY="sk-ant-..." \
    SENDGRID_API_KEY="SG..."
```

> If you change CORS to a custom DNS name (§5), re-run `fly secrets
> set CORS_ORIGINS=...` and `fly deploy` to pick up the new value.

### 3.5 Deploy backend

```bash
fly deploy \
    --app montgowork-staging-api \
    --config deploy/fly/fly.backend.toml \
    --dockerfile Dockerfile
```

Wait for "deployed successfully". Then confirm:

```bash
fly status --app montgowork-staging-api
curl https://montgowork-staging-api.fly.dev/health
# {"status":"healthy",...}
```

### 3.6 Deploy frontend

The frontend bakes `NEXT_PUBLIC_API_URL` at build time. Pass it as a
build-arg:

```bash
fly deploy \
    --app montgowork-staging-web \
    --config deploy/fly/fly.frontend.toml \
    --dockerfile Dockerfile.frontend \
    --build-arg NEXT_PUBLIC_API_URL=https://montgowork-staging-api.fly.dev
```

Confirm:

```bash
fly status --app montgowork-staging-web
curl -I https://montgowork-staging-web.fly.dev/
# HTTP/2 200
```

### 3.7 Seed demo data

> **Status:** T13.2 (demo seed) and T13.3 (qc-reset endpoint) are not
> yet implemented as of S13 kickoff. Until they land, run the existing
> dev seeder one-shot via `fly ssh`:

```bash
fly ssh console --app montgowork-staging-api
# inside the container:
python -m scripts.demo_seed_s12b   # if available
exit
```

Once T13.3 ships the `POST /api/admin/qc-reset` endpoint, prefer:

```bash
curl -X POST https://montgowork-staging-api.fly.dev/api/admin/qc-reset \
    -H "X-Admin-Key: <ADMIN_API_KEY value from §3.4>"
```

### 3.8 Update QC config + run smoke

Edit `.paircoder/qc/config.yaml` and replace the placeholder
`*.montgowork.example` URLs in the `staging:` block with the actual
Fly URLs (or your custom CNAME from §5):

```yaml
staging:
  frontend_url: https://montgowork-staging-web.fly.dev   # was: https://staging.montgowork.example
  backend_url: https://montgowork-staging-api.fly.dev    # was: https://staging-api.montgowork.example
  # ... rest unchanged ...
```

The `${STAGING_WORKER_MGM_SESSION}` / `${STAGING_ADMIN_KEY}` style
entries below those URLs are environment-variable references resolved
at QC-runner time — leave them alone and export the corresponding
values in your shell (or in a CI secret store) before running QC.

Then run the smoke check:

```bash
STAGING_FRONTEND_URL=https://montgowork-staging-web.fly.dev \
STAGING_API_URL=https://montgowork-staging-api.fly.dev \
    bash scripts/staging-smoke.sh
```

All checks must print `PASS`.

---

## 4. Subsequent Deploys

Once the apps exist and secrets are set, redeploy is two commands:

```bash
# Backend
fly deploy \
    --app montgowork-staging-api \
    --config deploy/fly/fly.backend.toml \
    --dockerfile Dockerfile

# Frontend (only if frontend changed; rebuild bakes the API URL)
fly deploy \
    --app montgowork-staging-web \
    --config deploy/fly/fly.frontend.toml \
    --dockerfile Dockerfile.frontend \
    --build-arg NEXT_PUBLIC_API_URL=https://montgowork-staging-api.fly.dev
```

Then re-run the smoke check (§3.8).

---

## 5. DNS — Pointing `staging.montgowork.*` at Fly

Default Fly URLs (`*.fly.dev`) work out of the box. For a custom DNS
hostname like `staging.montgowork.example`:

1. **Add the cert in Fly:**

   ```bash
   fly certs add staging.montgowork.example --app montgowork-staging-web
   fly certs add staging-api.montgowork.example --app montgowork-staging-api
   ```

2. **Read the required DNS records:**

   ```bash
   fly certs show staging.montgowork.example --app montgowork-staging-web
   ```

   Fly prints A / AAAA / CNAME / `_acme-challenge` requirements.

3. **Add records at your DNS provider:**
   - `staging.montgowork.example` CNAME → `montgowork-staging-web.fly.dev`
   - `staging-api.montgowork.example` CNAME → `montgowork-staging-api.fly.dev`
   - Plus the `_acme-challenge` TXT records Fly shows.

4. **Wait for cert** (usually <2 min):

   ```bash
   fly certs check staging.montgowork.example --app montgowork-staging-web
   ```

5. **Update CORS to the new frontend hostname:**

   ```bash
   fly secrets set --app montgowork-staging-api \
       CORS_ORIGINS=https://staging.montgowork.example
   fly deploy --app montgowork-staging-api \
       --config deploy/fly/fly.backend.toml \
       --dockerfile Dockerfile
   ```

6. **Update the frontend build with the new API hostname:**

   ```bash
   fly deploy \
       --app montgowork-staging-web \
       --config deploy/fly/fly.frontend.toml \
       --dockerfile Dockerfile.frontend \
       --build-arg NEXT_PUBLIC_API_URL=https://staging-api.montgowork.example
   ```

7. **Update `.paircoder/qc/config.yaml`** to the custom hostnames.

---

## 6. Rollback

Fly keeps every release. To roll back the backend:

```bash
fly releases list --app montgowork-staging-api
# Note the version number you want to return to (e.g. v23):
fly releases rollback v23 --app montgowork-staging-api
```

Frontend rollback is identical — substitute `--app
montgowork-staging-web`.

> **SQLite caveat:** rolling back a release does **not** roll back the
> database. If a release ran a destructive migration, you must restore
> from a volume snapshot (see §7.1).

---

## 7. Backups & Recovery

### 7.1 Volume snapshots

Fly snapshots volumes daily by default (5-day retention). To restore:

```bash
fly volumes snapshots list --app montgowork-staging-api
fly volumes create montgowork_staging_db_restore \
    --app montgowork-staging-api \
    --region iad \
    --snapshot-id <snapshot-id> \
    --size 1
# Then update fly.backend.toml's [[mounts]] source to the new volume
# name and redeploy.
```

For staging this is best-effort — the demo seed is reproducible via
T13.2/T13.3, so we don't pay for higher-retention backups.

### 7.2 Pulling a SQLite copy locally

```bash
fly ssh sftp shell --app montgowork-staging-api
# At the sftp> prompt:
get /app/data/montgowork.db ./staging-snapshot.db
quit
```

---

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Backend boots but `/health/ready` returns 503 | SQLite volume not mounted, or `DATABASE_URL` doesn't point at `/app/data/...` | `fly volumes list` — confirm volume exists and is attached. Check `fly logs` for SQLite errors. |
| `audit_hash_salt must be changed from the default value in production` on startup | `AUDIT_HASH_SALT` secret missing | `fly secrets set AUDIT_HASH_SALT="$(python -c 'import secrets;print(secrets.token_urlsafe(24))')"` then redeploy |
| `admin_api_key must be at least 32 characters` | `ADMIN_API_KEY` secret missing or too short | Same fix, but for `ADMIN_API_KEY`. The config validator only fires when `ENVIRONMENT=production` — staging runs as `staging` so this won't fire, but production will. |
| Frontend builds OK but API calls 404 | `NEXT_PUBLIC_API_URL` build-arg wasn't passed | Redeploy with `--build-arg NEXT_PUBLIC_API_URL=...`. The Next.js bundle must be rebuilt to pick up a new value. |
| CORS errors in browser console | `CORS_ORIGINS` doesn't include the actual frontend URL | `fly secrets set CORS_ORIGINS=https://your-frontend.example` then redeploy backend |
| `fly deploy` fails on `weasyprint` import | Missing native libs in the image | The project `Dockerfile` already installs `libpango-1.0-0`, `libcairo2`, etc. If a deploy fails here, check that you're using the project-root `Dockerfile`, not a custom one. |
| Build fails: "no such file: deploy/fly/fly.backend.toml" | Wrong working directory | Run from project root, not from `deploy/fly/`. |

### 8.1 Logs

```bash
fly logs --app montgowork-staging-api
fly logs --app montgowork-staging-web
```

### 8.2 Open a shell

```bash
fly ssh console --app montgowork-staging-api
```

---

## 9. Security Notes

- **Admin endpoints** (`/api/admin/*`) require `X-Admin-Key`. The
  smoke check asserts these return 401/403 without a key — never
  embed the admin key in the smoke script.
- **`/docs` and `/redoc`** are disabled when `ENVIRONMENT=production`.
  In staging (`ENVIRONMENT=staging`) they are exposed — that's
  intentional for QC. Do not promote a frontend env value of
  `staging` to production.
- **Secrets rotation:** rotate `ADMIN_API_KEY` and `AUDIT_HASH_SALT`
  any time team membership changes. After rotation, re-run the QC
  config update in §3.8.
- **HSTS** is set when `ENVIRONMENT=production`. We deliberately leave
  it off in staging so we can curl over HTTPS errors during cert
  bring-up without poisoning the browser cache.

---

## 10. Promotion to Production (Future)

When promoting this pattern to production:

1. Create separate Fly apps: `montgowork-prod-api` / `montgowork-prod-web`.
2. Set `ENVIRONMENT=production` (this enables the strict config
   validators — admin key length, audit salt, CORS origin checks).
3. Migrate off SQLite to managed Postgres before any horizontal
   scaling — see `docs/architecture.md`.
4. Set up Fly's Slack/email alerts on the production app's health
   checks.
5. Configure WAF / rate limiting at the Fly edge or via Cloudflare in
   front.

---

## 11. Acceptance Criteria Mapping (T13.128)

| AC item | Owner | Status |
|---------|-------|--------|
| Staging deployed at a stable URL | **User** (must run the commands in §3) | Pending — runbook ready |
| DB seeded with demo data via T13.2 + T13.3 | **User** post-deploy | Pending — also gated on T13.2/T13.3 landing |
| Every top-level route returns 200 in smoke check | Agent delivered `scripts/staging-smoke.sh`; user runs it after §3.8 | Script ready |
| Deploy + rollback runbook in `docs/runbooks/staging-deploy.md` | Agent | **Done** (this file) |
| `.paircoder/qc/config.yaml` `staging` profile points at the staging URL | User edits per §3.8 | Placeholder URLs (`*.montgowork.example`) in place; user replaces with real Fly URLs after deploy |
