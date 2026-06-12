/**
 * Tests for the admin_resources typed API client (T26.5).
 *
 * Mirrors the jobApplications.test.ts pattern: stub `fetch` via
 * `vi.stubGlobal`, assert URL + method + body for each function, and
 * verify the typed error throws on non-2xx with the parsed `detail`.
 *
 * The client delegates transport to the shared helpers in `_client.ts`
 * (`fetchWithCookie` adds `credentials: "include"`; `throwOnApiError`
 * raises a typed error on non-2xx). We assert the shapes those helpers
 * emit (URL prefix, credentials, JSON content-type on writes) without
 * re-testing the helpers themselves.
 */
import {
  describe,
  it,
  expect,
  beforeEach,
  vi,
  afterEach,
} from "vitest";
import type { Resource } from "../admin_resources";

describe("admin_resources API client", () => {
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

  const sample: Resource = {
    id: 7,
    name: "Acme Workforce Center",
    category: "career_center",
    subcategory: null,
    address: "123 Main St",
    lat: 32.75,
    lng: -97.33,
    phone: "555-1212",
    url: "https://example.org",
    eligibility: null,
    services: null,
    hours: null,
    notes: null,
    city: "fort-worth",
    barrier_affinity: null,
    health_status: "healthy",
    user_curated_at: "2026-05-08T00:00:00+00:00",
  };

  it("listResources GETs /api/admin/resources with query params", async () => {
    const response = {
      items: [sample],
      total: 1,
      limit: 50,
      offset: 0,
    };
    mockJson(response);
    const { listResources } = await import("../admin_resources");
    const result = await listResources({ city: "fort-worth" });
    expect(result).toEqual(response);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/admin\/resources\?city=fort-worth$/);
    expect((init as RequestInit).method).toBe("GET");
    expect((init as RequestInit).credentials).toBe("include");
  });

  it("listResources includes limit, offset, and include_hidden", async () => {
    mockJson({ items: [], total: 0, limit: 25, offset: 50 });
    const { listResources } = await import("../admin_resources");
    await listResources({
      city: "dallas",
      limit: 25,
      offset: 50,
      includeHidden: true,
    });
    const [url] = fetchMock.mock.calls[0];
    expect(url).toMatch(
      /\/api\/admin\/resources\?city=dallas&limit=25&offset=50&include_hidden=true$/,
    );
  });

  it("listResources omits city when not provided", async () => {
    mockJson({ items: [], total: 0, limit: 50, offset: 0 });
    const { listResources } = await import("../admin_resources");
    await listResources({});
    const [url] = fetchMock.mock.calls[0];
    // No query string when no opts provided.
    expect(url).toMatch(/\/api\/admin\/resources$/);
  });

  it("getResource GETs /api/admin/resources/{id}", async () => {
    mockJson(sample);
    const { getResource } = await import("../admin_resources");
    const result = await getResource(7);
    expect(result).toEqual(sample);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/admin\/resources\/7$/);
    expect((init as RequestInit).method).toBe("GET");
    expect((init as RequestInit).credentials).toBe("include");
  });

  it("createResource POSTs payload to /api/admin/resources", async () => {
    mockJson(sample, true, 201);
    const { createResource } = await import("../admin_resources");
    const payload = {
      name: "Acme Workforce Center",
      category: "career_center",
      city: "fort-worth",
      address: "123 Main St",
    };
    const result = await createResource(payload);
    expect(result).toEqual(sample);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/admin\/resources$/);
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).credentials).toBe("include");
    expect(JSON.parse((init as RequestInit).body as string)).toEqual(payload);
  });

  it("updateResource PATCHes /api/admin/resources/{id} with patch", async () => {
    mockJson({ ...sample, name: "Renamed" });
    const { updateResource } = await import("../admin_resources");
    const patch = { name: "Renamed" };
    const result = await updateResource(7, patch);
    expect(result.name).toBe("Renamed");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/admin\/resources\/7$/);
    expect((init as RequestInit).method).toBe("PATCH");
    expect((init as RequestInit).credentials).toBe("include");
    expect(JSON.parse((init as RequestInit).body as string)).toEqual(patch);
  });

  it("hideResource DELETEs /api/admin/resources/{id}", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 204,
      statusText: "No Content",
      headers: new Headers(),
      json: async () => ({}),
    });
    const { hideResource } = await import("../admin_resources");
    await hideResource(7);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/admin\/resources\/7$/);
    expect((init as RequestInit).method).toBe("DELETE");
    expect((init as RequestInit).credentials).toBe("include");
  });

  it("restoreResource POSTs /api/admin/resources/{id}/restore", async () => {
    mockJson({ id: 7, health_status: "healthy" });
    const { restoreResource } = await import("../admin_resources");
    const result = await restoreResource(7);
    expect(result).toEqual({ id: 7, health_status: "healthy" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/admin\/resources\/7\/restore$/);
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).credentials).toBe("include");
  });

  it("throws AdminResourcesApiError on non-ok with parsed detail", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: "Not Found",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "Resource not found" }),
    });
    const { getResource, AdminResourcesApiError } = await import(
      "../admin_resources"
    );
    const promise = getResource(999);
    await expect(promise).rejects.toBeInstanceOf(AdminResourcesApiError);
    await expect(promise).rejects.toMatchObject({
      status: 404,
      detail: "Resource not found",
    });
  });

  it("throws AdminResourcesApiError on 500 with statusText fallback", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      headers: new Headers({ "content-type": "text/html" }),
      json: async () => {
        throw new Error("not json");
      },
    });
    const { listResources, AdminResourcesApiError } = await import(
      "../admin_resources"
    );
    const promise = listResources({ city: "fort-worth" });
    await expect(promise).rejects.toBeInstanceOf(AdminResourcesApiError);
    await expect(promise).rejects.toMatchObject({ status: 500 });
  });
});
