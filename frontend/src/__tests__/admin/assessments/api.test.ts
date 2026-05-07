import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

/**
 * Tests for the typed assessments API client (T23.7).
 *
 * Covers the four functions the reviewer dashboard consumes:
 *   - listPendingAssessments()
 *   - getAssessmentVersion(versionId)
 *   - reviewAssessment(versionId, action, comment)
 *   - publishAssessment(versionId)
 *
 * The client mirrors `lib/api/auth.ts` — `_fetchWithTimeout` with the
 * `_composeSignal` fix from S22 review-fixes — but only the public
 * surface is asserted here.
 */
describe("assessments API client", () => {
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

  it("listPendingAssessments GETs /api/admin/assessments/pending", async () => {
    const wire = [
      {
        version_id: 11,
        assessment_id: 1,
        version_number: 2,
        status: "in_review",
        drafted_by: 7,
        created_at: "2026-05-01T00:00:00Z",
        slug: "vocational-screen-v2",
        kind: "screening",
        track: "vocational",
      },
    ];
    mockJson(wire);
    const { listPendingAssessments } = await import("@/lib/api/assessments");
    const rows = await listPendingAssessments();
    expect(rows).toEqual(wire);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/admin\/assessments\/pending$/);
    expect((init as RequestInit | undefined)?.method ?? "GET").toBe("GET");
    expect((init as RequestInit | undefined)?.credentials).toBe("include");
  });

  it("listPendingAssessments throws AssessmentsApiError on 403", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 403,
      statusText: "Forbidden",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "missing role" }),
    });
    const { listPendingAssessments, AssessmentsApiError } = await import(
      "@/lib/api/assessments"
    );
    const promise = listPendingAssessments();
    await expect(promise).rejects.toBeInstanceOf(AssessmentsApiError);
    await expect(promise).rejects.toMatchObject({ status: 403 });
  });

  it("getAssessmentVersion GETs /api/admin/assessments/{id}", async () => {
    const wire = {
      version_id: 11,
      assessment_id: 1,
      version_number: 2,
      status: "in_review",
      drafted_by: 7,
      reviewed_by: null,
      approved_by: null,
      published_at: null,
      retired_at: null,
      created_at: "2026-05-01T00:00:00Z",
      questions: [
        {
          id: 100,
          position: 1,
          prompt: "Q1?",
          kind: "scale",
          rubric_json: {},
          scoring_weight: 1.0,
        },
      ],
    };
    mockJson(wire);
    const { getAssessmentVersion } = await import("@/lib/api/assessments");
    const v = await getAssessmentVersion(11);
    expect(v).toEqual(wire);
    const [url] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/admin\/assessments\/11$/);
  });

  it("getAssessmentVersion throws AssessmentsApiError on 404", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: "Not Found",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "Version not found" }),
    });
    const { getAssessmentVersion, AssessmentsApiError } = await import(
      "@/lib/api/assessments"
    );
    const promise = getAssessmentVersion(404);
    await expect(promise).rejects.toBeInstanceOf(AssessmentsApiError);
    await expect(promise).rejects.toMatchObject({ status: 404 });
  });

  it("reviewAssessment POSTs to /{id}/review with action+comment", async () => {
    mockJson({ review_id: 99 });
    const { reviewAssessment } = await import("@/lib/api/assessments");
    const out = await reviewAssessment(11, "approve", "looks good");
    expect(out).toEqual({ review_id: 99 });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/admin\/assessments\/11\/review$/);
    expect((init as RequestInit).method).toBe("POST");
    expect(JSON.parse((init as RequestInit).body as string)).toEqual({
      action: "approve",
      comment: "looks good",
    });
  });

  it("reviewAssessment omits comment when null", async () => {
    mockJson({ review_id: 100 });
    const { reviewAssessment } = await import("@/lib/api/assessments");
    await reviewAssessment(11, "reject", null);
    const [, init] = fetchMock.mock.calls[0];
    expect(JSON.parse((init as RequestInit).body as string)).toEqual({
      action: "reject",
      comment: null,
    });
  });

  it("reviewAssessment throws AssessmentsApiError on 409", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 409,
      statusText: "Conflict",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "cannot review a published version" }),
    });
    const { reviewAssessment, AssessmentsApiError } = await import(
      "@/lib/api/assessments"
    );
    const promise = reviewAssessment(11, "approve", null);
    await expect(promise).rejects.toBeInstanceOf(AssessmentsApiError);
    await expect(promise).rejects.toMatchObject({ status: 409 });
  });

  it("publishAssessment POSTs to /{id}/publish", async () => {
    const wire = {
      assessment_id: 1,
      version_id: 11,
      version_number: 2,
      published_at: "2026-05-02T12:00:00Z",
      slug: "vocational-screen-v2",
      public_url: "/api/assessments/vocational-screen-v2",
    };
    mockJson(wire);
    const { publishAssessment } = await import("@/lib/api/assessments");
    const out = await publishAssessment(11);
    expect(out).toEqual(wire);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/admin\/assessments\/11\/publish$/);
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).credentials).toBe("include");
  });

  it("publishAssessment throws AssessmentsApiError on 403 (non-admin)", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 403,
      statusText: "Forbidden",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "admin role required" }),
    });
    const { publishAssessment, AssessmentsApiError } = await import(
      "@/lib/api/assessments"
    );
    const promise = publishAssessment(11);
    await expect(promise).rejects.toBeInstanceOf(AssessmentsApiError);
    await expect(promise).rejects.toMatchObject({ status: 403 });
  });
});
