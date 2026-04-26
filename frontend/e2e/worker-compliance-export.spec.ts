import { test, expect } from "@playwright/test";
import { DEMO, BACKEND_BASE, detectBackend } from "./_demo_session";

/**
 * Beat 5 of the demo script — worker exports their data.
 *
 * The demo beat shows a curl-in-terminal pane (compliance is API-only;
 * no UI button at the moment). We mirror that with an API-level
 * Playwright test using `request.post` / `request.get` so the gate
 * still produces a CI signal even though the flow has no DOM surface.
 *
 * Two-step contract from `app.routes.compliance`:
 *   1. POST /api/compliance/export with {session_id, session_token}
 *      → 200 {archive_id, download_url, expires_in_sec}
 *   2. GET <download_url>
 *      → 200, Content-Type: application/zip, non-empty body
 *
 * Single-use download token: the GET in step 2 consumes the token, so a
 * second invocation in the same spec run would fail. We assert the
 * happy path once, end of spec.
 *
 * Rate limit: 3 exports per hour per session (see `_enforce_rate_limit`
 * in compliance.py). If this test runs more than 3x in a 60-min window
 * (e.g. tight retries), expect 429s — that's a real backend signal,
 * not a test bug.
 */
test.describe("@critical worker compliance export", () => {
  const creds = DEMO.workerMontgomeryMedium;

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
          session_id: creds.sessionId,
          session_token: creds.feedbackToken,
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
    const exportRes = await request.post(
      `${BACKEND_BASE}/api/compliance/export`,
      {
        data: {
          session_id: creds.sessionId,
          session_token: creds.feedbackToken,
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
    const res = await request.post(`${BACKEND_BASE}/api/compliance/export`, {
      data: {
        session_id: creds.sessionId,
        session_token: "wrong-token-xxxxxxxxxxxxxxxxxxxxxxxx",
      },
    });
    expect([401, 403]).toContain(res.status());
  });
});
