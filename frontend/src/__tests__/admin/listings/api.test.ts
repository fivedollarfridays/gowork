import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

/**
 * Tests for the typed listing-claims API client (T24.9).
 *
 * Covers the four functions the admin claim-review dashboard consumes:
 *   - listPendingClaims()
 *   - getClaim(claimId)
 *   - approveClaim(claimId)
 *   - rejectClaim(claimId)
 *
 * Mirrors the assessments API client pattern (T23.7): `_fetchWithTimeout`
 * + `credentials: include` + a single typed error class so callers can
 * branch on `.status` (403 → not-authorised, 404 → missing).
 */
describe("listing claims API client", () => {
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

  it("listPendingClaims GETs /api/employers/admin/claims/pending", async () => {
    const wire = [
      {
        claim_id: 5,
        claimant_email: "x@example.com",
        listing_id: 11,
        listing_title: "Forklift",
        employer_account_id: 7,
        employer_domain: "acme.com",
        verification_tier: "admin_reviewed",
        intake_completed_at: null,
        claim_created_at: "2026-05-01T00:00:00Z",
      },
    ];
    mockJson(wire);
    const { listPendingClaims } = await import("@/lib/api/listing_claims");
    const rows = await listPendingClaims();
    expect(rows).toEqual(wire);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/employers\/admin\/claims\/pending$/);
    expect((init as RequestInit | undefined)?.method ?? "GET").toBe("GET");
    expect((init as RequestInit | undefined)?.credentials).toBe("include");
  });

  it("listPendingClaims throws ListingClaimsApiError on 403", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 403,
      statusText: "Forbidden",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "missing role" }),
    });
    const { listPendingClaims, ListingClaimsApiError } = await import(
      "@/lib/api/listing_claims"
    );
    const promise = listPendingClaims();
    await expect(promise).rejects.toBeInstanceOf(ListingClaimsApiError);
    await expect(promise).rejects.toMatchObject({ status: 403 });
  });

  it("getClaim GETs /api/employers/admin/claims/{claimId}", async () => {
    const wire = {
      claim_id: 5,
      claimant_email: "x@example.com",
      listing_id: 11,
      listing_title: "Forklift",
      listing_company: "ACME",
      employer_account_id: 7,
      employer_domain: "acme.com",
      employer_name: "acme.com",
      employer_status: "admin_review",
      verification_tier: "admin_reviewed",
      intake_json: null,
      intake_completed_at: null,
      verification_id: 2,
      verified_at: "2026-05-01T00:00:00Z",
      claim_created_at: "2026-05-01T00:00:00Z",
      expires_at: "2026-05-01T00:15:00Z",
      used_at: null,
    };
    mockJson(wire);
    const { getClaim } = await import("@/lib/api/listing_claims");
    const v = await getClaim(5);
    expect(v).toEqual(wire);
    const [url] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/employers\/admin\/claims\/5$/);
  });

  it("getClaim throws ListingClaimsApiError on 404", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: "Not Found",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "claim not found" }),
    });
    const { getClaim, ListingClaimsApiError } = await import(
      "@/lib/api/listing_claims"
    );
    const promise = getClaim(404);
    await expect(promise).rejects.toBeInstanceOf(ListingClaimsApiError);
    await expect(promise).rejects.toMatchObject({ status: 404 });
  });

  it("approveClaim POSTs to /{claimId}/approve", async () => {
    mockJson({
      claim_id: 5,
      employer_account_id: 7,
      verification_status: "verified",
      verified_at: "2026-05-02T12:00:00Z",
    });
    const { approveClaim } = await import("@/lib/api/listing_claims");
    const out = await approveClaim(5);
    expect(out.verification_status).toBe("verified");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/employers\/admin\/claims\/5\/approve$/);
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).credentials).toBe("include");
  });

  it("approveClaim throws ListingClaimsApiError on 403", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 403,
      statusText: "Forbidden",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "admin role required" }),
    });
    const { approveClaim, ListingClaimsApiError } = await import(
      "@/lib/api/listing_claims"
    );
    const promise = approveClaim(5);
    await expect(promise).rejects.toBeInstanceOf(ListingClaimsApiError);
    await expect(promise).rejects.toMatchObject({ status: 403 });
  });

  it("rejectClaim DELETEs /{claimId}", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 204,
      statusText: "No Content",
      headers: new Headers(),
      json: async () => ({}),
    });
    const { rejectClaim } = await import("@/lib/api/listing_claims");
    await rejectClaim(5);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/employers\/admin\/claims\/5$/);
    expect((init as RequestInit).method).toBe("DELETE");
    expect((init as RequestInit).credentials).toBe("include");
  });

  it("rejectClaim throws ListingClaimsApiError on 404", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: "Not Found",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "claim not found" }),
    });
    const { rejectClaim, ListingClaimsApiError } = await import(
      "@/lib/api/listing_claims"
    );
    const promise = rejectClaim(5);
    await expect(promise).rejects.toBeInstanceOf(ListingClaimsApiError);
    await expect(promise).rejects.toMatchObject({ status: 404 });
  });
});
