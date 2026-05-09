/**
 * Vitest contract tests for the admin-feedback typed API client (T26.6).
 *
 * Mirrors the `documents.test.ts` pattern: stub `fetch`, assert URL +
 * method + body per function, and verify the typed error class throws
 * on non-2xx with the backend `detail` propagated. Each test uses
 * dynamic `import()` so the per-test fetch stub is in place before the
 * client module is evaluated.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import type {
  FlaggedResource,
  VisitFeedback,
  VisitFeedbackListResponse,
} from "../admin_feedback";

describe("admin_feedback API client", () => {
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

  const flaggedSample: FlaggedResource = {
    id: 42,
    name: "Sample Center",
    category: "social_service",
    city: "fortworth",
    health_status: "flagged",
    address: "123 Main St",
    phone: "555-1212",
    url: "https://example.com",
    recent_negative_feedback: [
      {
        session_id: "sess-1",
        barrier_type: "transportation",
        submitted_at: "2026-04-15T12:00:00Z",
      },
    ],
  };

  const visitSample: VisitFeedback = {
    id: 7,
    session_id: "sess-1",
    submitted_at: "2026-04-20T12:00:00Z",
    made_it_to_center: 1,
    outcomes: "intake_completed",
    plan_accuracy: 4,
    free_text: "All good",
    reviewed: 0,
    action_taken: null,
  };

  it("listFlagged hits GET /api/admin/feedback/flagged with city query", async () => {
    mockJson({ items: [flaggedSample] });
    const { listFlagged } = await import("../admin_feedback");
    const result = await listFlagged("fortworth");
    expect(result).toEqual({ items: [flaggedSample] });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/admin\/feedback\/flagged\?city=fortworth$/);
    expect((init as RequestInit | undefined)?.method ?? "GET").toBe("GET");
    expect((init as RequestInit | undefined)?.credentials).toBe("include");
  });

  it("listFlagged URL-encodes the city slug", async () => {
    mockJson({ items: [] });
    const { listFlagged } = await import("../admin_feedback");
    await listFlagged("New City");
    const [url] = fetchMock.mock.calls[0];
    expect(url).toMatch(
      /\/api\/admin\/feedback\/flagged\?city=New(?:%20|\+)City$/,
    );
  });

  it("approveFlagged POSTs to /flagged/{id}/approve", async () => {
    mockJson({ id: 42, health_status: "healthy" });
    const { approveFlagged } = await import("../admin_feedback");
    const result = await approveFlagged(42);
    expect(result).toEqual({ id: 42, health_status: "healthy" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/admin\/feedback\/flagged\/42\/approve$/);
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).credentials).toBe("include");
    expect((init as RequestInit).body).toBeUndefined();
  });

  it("confirmHide POSTs to /flagged/{id}/confirm-hide", async () => {
    mockJson({ id: 42, health_status: "hidden" });
    const { confirmHide } = await import("../admin_feedback");
    const result = await confirmHide(42);
    expect(result).toEqual({ id: 42, health_status: "hidden" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/admin\/feedback\/flagged\/42\/confirm-hide$/);
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).credentials).toBe("include");
    expect((init as RequestInit).body).toBeUndefined();
  });

  it("listVisits with no opts hits /api/admin/feedback/visits with no query", async () => {
    const payload: VisitFeedbackListResponse = {
      items: [visitSample],
      total: 1,
      limit: 50,
      offset: 0,
    };
    mockJson(payload);
    const { listVisits } = await import("../admin_feedback");
    const result = await listVisits();
    expect(result).toEqual(payload);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/admin\/feedback\/visits$/);
    expect((init as RequestInit | undefined)?.method ?? "GET").toBe("GET");
    expect((init as RequestInit | undefined)?.credentials).toBe("include");
  });

  it("listVisits serializes reviewed=true as boolean string", async () => {
    mockJson({ items: [], total: 0, limit: 25, offset: 10 });
    const { listVisits } = await import("../admin_feedback");
    await listVisits({ reviewed: true, limit: 25, offset: 10 });
    const [url] = fetchMock.mock.calls[0];
    expect(url).toMatch(
      /\/api\/admin\/feedback\/visits\?reviewed=true&limit=25&offset=10$/,
    );
  });

  it("listVisits serializes reviewed=false explicitly", async () => {
    mockJson({ items: [], total: 0, limit: 50, offset: 0 });
    const { listVisits } = await import("../admin_feedback");
    await listVisits({ reviewed: false });
    const [url] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/admin\/feedback\/visits\?reviewed=false$/);
  });

  it("listVisits omits unspecified params", async () => {
    mockJson({ items: [], total: 0, limit: 50, offset: 0 });
    const { listVisits } = await import("../admin_feedback");
    await listVisits({ limit: 100 });
    const [url] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/admin\/feedback\/visits\?limit=100$/);
  });

  it("markVisitReviewed POSTs with action_taken body when provided", async () => {
    mockJson({ id: 7, reviewed: true, action_taken: "called" });
    const { markVisitReviewed } = await import("../admin_feedback");
    const result = await markVisitReviewed(7, "called");
    expect(result).toEqual({ id: 7, reviewed: true, action_taken: "called" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/admin\/feedback\/visits\/7\/mark-reviewed$/);
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).credentials).toBe("include");
    expect(JSON.parse((init as RequestInit).body as string)).toEqual({
      action_taken: "called",
    });
    const headers = (init as RequestInit).headers as Record<string, string>;
    expect(headers["Content-Type"]).toBe("application/json");
  });

  it("markVisitReviewed POSTs with empty body when action_taken omitted", async () => {
    mockJson({ id: 7, reviewed: true, action_taken: null });
    const { markVisitReviewed } = await import("../admin_feedback");
    await markVisitReviewed(7);
    const [, init] = fetchMock.mock.calls[0];
    expect((init as RequestInit).method).toBe("POST");
    // Empty body (no action_taken) — backend treats this as `reviewed=1` with
    // action_taken NULL. We send `{}` so the route sees a parseable JSON body.
    expect((init as RequestInit).body).toBeUndefined();
  });

  it("throws AdminFeedbackApiError on non-2xx with detail propagated", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 403,
      statusText: "Forbidden",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "admin role required" }),
    });
    const { listFlagged, AdminFeedbackApiError } = await import(
      "../admin_feedback"
    );
    await expect(listFlagged("fortworth")).rejects.toBeInstanceOf(
      AdminFeedbackApiError,
    );
  });

  it("AdminFeedbackApiError carries status and detail fields", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: "Not Found",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "Resource not found" }),
    });
    const { approveFlagged, AdminFeedbackApiError } = await import(
      "../admin_feedback"
    );
    try {
      await approveFlagged(999);
      throw new Error("expected throw");
    } catch (err) {
      expect(err).toBeInstanceOf(AdminFeedbackApiError);
      const e = err as InstanceType<typeof AdminFeedbackApiError>;
      expect(e.status).toBe(404);
      expect(e.detail).toBe("Resource not found");
      expect(e.message).toMatch(/Resource not found/);
    }
  });
});
