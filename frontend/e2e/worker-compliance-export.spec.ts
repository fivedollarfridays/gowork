import { test, expect } from "@playwright/test";
import { DEMO, BACKEND_BASE, detectBackend } from "./_demo_session";

/**
 * Beat 5 of the demo script — worker exports their data.
 *
 * Compliance is API-only (no UI surface), so this gate exercises the
 * two-step contract from `app.routes.compliance` directly:
 *   1. POST /api/compliance/export → 200 + signed single-use download URL
 *   2. GET <download_url>          → 200 application/zip
 *
 * Rate limit: 3 export POSTs per hour per session id (in-memory in
 * compliance.py:_enforce_rate_limit). Each test below uses a distinct
 * demo session so retries don't flake on 429.
 */
test.describe("@critical worker compliance export", () => {
  const credsIssue = DEMO.workerMontgomeryMedium;
  const credsZip = DEMO.workerMontgomeryHard;
  const credsAuth = DEMO.workerMontgomeryMedium;

  test.beforeAll(async ({ request }) => {
    const reason = await detectBackend(request);
    test.skip(reason !== null, reason ?? "");
  });

  test("POST /api/compliance/export issues a single-use download URL", async ({
    request,
  }) => {
    const exportRes = await request.post(
      `${BACKEND_BASE}/api/compliance/export`,
      {
        data: {
          session_id: credsIssue.sessionId,
          session_token: credsIssue.feedbackToken,
        },
      },
    );

    expect(exportRes.status()).toBe(200);

    const body = await exportRes.json();
    expect(body).toHaveProperty("archive_id");
    expect(body).toHaveProperty("download_url");
    expect(body.download_url).toMatch(
      /^\/api\/compliance\/export\/download\?token=/,
    );
    expect(typeof body.expires_in_sec).toBe("number");
    expect(body.expires_in_sec).toBeGreaterThan(0);
  });

  test("download URL streams a non-empty ZIP archive", async ({ request }) => {
    // Mints a fresh token inside the test (single-use enforcement is
    // working as designed; this test must not reuse the one minted by
    // the test above). Uses the hard-stall demo session to avoid
    // sharing the medium session's per-hour quota.
    const exportRes = await request.post(
      `${BACKEND_BASE}/api/compliance/export`,
      {
        data: {
          session_id: credsZip.sessionId,
          session_token: credsZip.feedbackToken,
        },
      },
    );
    expect(exportRes.status()).toBe(200);
    const { download_url } = await exportRes.json();

    const dlRes = await request.get(`${BACKEND_BASE}${download_url}`);
    expect(dlRes.status()).toBe(200);
    expect(dlRes.headers()["content-type"]).toContain("application/zip");

    const buf = await dlRes.body();
    expect(buf.byteLength).toBeGreaterThan(0);
  });

  test("invalid session_token returns 401 without leaking a URL", async ({
    request,
  }) => {
    // verify_token runs before _enforce_rate_limit, so this 401 path
    // does not consume a rate-limit slot — safe to share a session id.
    const res = await request.post(`${BACKEND_BASE}/api/compliance/export`, {
      data: {
        session_id: credsAuth.sessionId,
        session_token: "wrong-token-xxxxxxxxxxxxxxxxxxxxxxxx",
      },
    });
    expect([401, 403]).toContain(res.status());
  });
});
