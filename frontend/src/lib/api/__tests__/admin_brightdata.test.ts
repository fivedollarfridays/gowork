/**
 * Tests for the admin_brightdata typed API client (T26.7).
 *
 * Mirrors the vitest stub-fetch convention used by sibling clients
 * (appointments.test.ts, documents.test.ts) — `vi.stubGlobal("fetch", ...)`
 * + per-test `mockJson` helper. Verifies URL, method, body, return
 * parsing, and the typed error throw on non-2xx.
 *
 * Endpoint shape sourced directly from backend/app/routes/brightdata.py
 * (T26.4 — gate-migrated to `require_role("admin")` so the cookie session
 * reaches the gate). Wire types match
 * backend/app/integrations/brightdata/types.py 1:1.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

describe("admin_brightdata API client", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  function mockJson(body: unknown, ok = true, status = 200) {
    fetchMock.mockResolvedValueOnce({
      ok,
      status,
      statusText: ok ? "OK" : "Error",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => body,
    });
  }

  it("triggerCrawl POSTs to /api/brightdata/crawl with urls payload and returns parsed response", async () => {
    const responseBody = {
      snapshot_id: "snap_abc123",
      status: "starting",
      message: "Crawl triggered",
    };
    mockJson(responseBody);
    const { triggerCrawl } = await import("../admin_brightdata");
    const result = await triggerCrawl({
      urls: ["https://example.com/jobs"],
    });
    expect(result).toEqual(responseBody);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/brightdata\/crawl$/);
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).credentials).toBe("include");
    expect(JSON.parse((init as RequestInit).body as string)).toEqual({
      urls: ["https://example.com/jobs"],
    });
  });

  it("getCrawlStatus GETs /api/brightdata/status/{snapshot_id} and returns parsed response", async () => {
    const responseBody = {
      snapshot_id: "snap_abc123",
      status: "running",
      progress_pct: 42.5,
      jobs_found: null,
      message: "Crawl in progress",
    };
    mockJson(responseBody);
    const { getCrawlStatus } = await import("../admin_brightdata");
    const result = await getCrawlStatus("snap_abc123");
    expect(result).toEqual(responseBody);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/brightdata\/status\/snap_abc123$/);
    expect((init as RequestInit | undefined)?.method ?? "GET").toBe("GET");
    expect((init as RequestInit).credentials).toBe("include");
  });

  it("getCrawlStatus URL-encodes the snapshot id segment", async () => {
    mockJson({
      snapshot_id: "weird/id",
      status: "ready",
      jobs_found: 3,
      message: "done",
    });
    const { getCrawlStatus } = await import("../admin_brightdata");
    await getCrawlStatus("weird/id");
    const [url] = fetchMock.mock.calls[0];
    // Must encode '/' as %2F so the snapshot_id stays a single path
    // segment (the backend Path() pattern rejects '/').
    expect(url).toMatch(/\/api\/brightdata\/status\/weird%2Fid$/);
  });

  it("triggerCrawl throws AdminBrightDataApiError with status + detail on non-2xx", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 502,
      statusText: "Bad Gateway",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "BrightData upstream failed" }),
    });
    const { triggerCrawl, AdminBrightDataApiError } = await import(
      "../admin_brightdata"
    );
    await expect(
      triggerCrawl({ urls: ["https://example.com/jobs"] }),
    ).rejects.toBeInstanceOf(AdminBrightDataApiError);

    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 502,
      statusText: "Bad Gateway",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "BrightData upstream failed" }),
    });
    await expect(
      triggerCrawl({ urls: ["https://example.com/jobs"] }),
    ).rejects.toMatchObject({
      status: 502,
      detail: "BrightData upstream failed",
    });
  });

  it("getCrawlStatus throws AdminBrightDataApiError on non-2xx", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: "Not Found",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "snapshot not found" }),
    });
    const { getCrawlStatus, AdminBrightDataApiError } = await import(
      "../admin_brightdata"
    );
    await expect(getCrawlStatus("nope")).rejects.toBeInstanceOf(
      AdminBrightDataApiError,
    );
  });
});
