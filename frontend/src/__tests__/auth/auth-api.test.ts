import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

describe("auth API client", () => {
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

  it("requestMagicLink POSTs to /api/auth/magic-link with email", async () => {
    mockJson({});
    const { requestMagicLink } = await import("@/lib/api/auth");
    await requestMagicLink("user@example.com");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/auth\/magic-link$/);
    expect((init as RequestInit).method).toBe("POST");
    expect(JSON.parse((init as RequestInit).body as string)).toEqual({
      email: "user@example.com",
    });
    expect(
      (init as RequestInit).headers as Record<string, string>,
    ).toMatchObject({ "Content-Type": "application/json" });
  });

  it("requestMagicLink resolves on 202 Accepted (no enumeration)", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 202,
      statusText: "Accepted",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({}),
    });
    const { requestMagicLink } = await import("@/lib/api/auth");
    await expect(requestMagicLink("user@example.com")).resolves.toBeUndefined();
  });

  it("claimMagicLink GETs /api/auth/claim with encoded token", async () => {
    mockJson({ account_id: 7, claimed_session_ids: ["sess-1"] });
    const { claimMagicLink } = await import("@/lib/api/auth");
    const result = await claimMagicLink("abc 123");
    expect(result).toEqual({ account_id: 7, claimed_session_ids: ["sess-1"] });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/auth\/claim\?token=abc%20123$/);
    expect((init as RequestInit | undefined)?.method ?? "GET").toBe("GET");
    expect((init as RequestInit | undefined)?.credentials).toBe("include");
  });

  it("claimMagicLink throws ClaimError 'invalid' on 401", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "invalid" }),
    });
    const { claimMagicLink, ClaimError } = await import("@/lib/api/auth");
    const promise = claimMagicLink("bad-token");
    await expect(promise).rejects.toBeInstanceOf(ClaimError);
    await expect(promise).rejects.toMatchObject({ kind: "invalid", status: 401 });
  });

  it("claimMagicLink throws ClaimError 'conflict' on 409", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 409,
      statusText: "Conflict",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "cross-account conflict" }),
    });
    const { claimMagicLink, ClaimError } = await import("@/lib/api/auth");
    const promise = claimMagicLink("conflict-token");
    await expect(promise).rejects.toBeInstanceOf(ClaimError);
    await expect(promise).rejects.toMatchObject({ kind: "conflict", status: 409 });
  });

  it("claimMagicLink throws ClaimError 'unknown' on 500", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Server Error",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "boom" }),
    });
    const { claimMagicLink, ClaimError } = await import("@/lib/api/auth");
    const promise = claimMagicLink("tkn");
    await expect(promise).rejects.toBeInstanceOf(ClaimError);
    await expect(promise).rejects.toMatchObject({ kind: "unknown", status: 500 });
  });
});
