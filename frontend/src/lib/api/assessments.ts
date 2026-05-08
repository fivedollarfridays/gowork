/**
 * Typed API client for the assessment authoring pipeline (T23.7).
 *
 * Four endpoints, all mounted under ``/api/admin/assessments`` and gated
 * by reviewer or admin roles on the backend (T23.4 / T23.5):
 *
 *   - GET  /pending                 → reviewer queue (track-aware)
 *   - GET  /{version_id}            → full version + questions
 *   - POST /{version_id}/review     → record a review action
 *   - POST /{version_id}/publish    → admin-only publish
 *
 * Mirrors the fetch + timeout convention from `lib/api/auth.ts`,
 * including the `_composeSignal` fix from S22 review-fixes that keeps
 * the timeout active when the caller passes their own AbortSignal.
 *
 * All non-2xx responses raise :class:`AssessmentsApiError` so callers
 * can branch on `.status` (403 → not-authorised, 404 → missing,
 * 409 → state-machine conflict).
 */

import { fetchWithTimeout } from "./_client";

/* -------------------------------------------------------------------------
 * Wire types — match the backend Pydantic / dict shapes 1:1.
 * ------------------------------------------------------------------------- */

export interface PendingAssessment {
  version_id: number;
  assessment_id: number;
  version_number: number;
  status: string;
  drafted_by: number;
  created_at: string;
  slug: string;
  kind: string;
  track: string;
}

export interface AssessmentQuestion {
  id: number;
  position: number;
  prompt: string;
  kind: string;
  rubric_json: Record<string, unknown> | null;
  scoring_weight: number;
}

export interface AssessmentVersion {
  version_id: number;
  assessment_id: number;
  version_number: number;
  status: string;
  drafted_by: number;
  reviewed_by: number | null;
  approved_by: number | null;
  published_at: string | null;
  retired_at: string | null;
  created_at: string;
  questions: AssessmentQuestion[];
}

export type ReviewAction = "approve" | "reject" | "request_revision";

export interface ReviewResponse {
  review_id: number;
}

export interface PublishResponse {
  assessment_id: number;
  version_id: number;
  version_number: number;
  published_at: string;
  slug: string;
  public_url: string;
}

/* -------------------------------------------------------------------------
 * Error class — single discriminator for callers (status code).
 * ------------------------------------------------------------------------- */

export class AssessmentsApiError extends Error {
  readonly status: number;
  readonly detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.name = "AssessmentsApiError";
    this.status = status;
    this.detail = detail;
  }
}

/* -------------------------------------------------------------------------
 * Internal fetch helper — every admin-assessments call goes through the
 * cookie session, so this wrapper bakes in `credentials: "include"`
 * before delegating to the shared transport (`./_client.ts`).
 * ------------------------------------------------------------------------- */

async function _fetchWithTimeout(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  return fetchWithTimeout(path, { credentials: "include", ...init });
}

async function _throwOnError(res: Response): Promise<void> {
  if (res.ok) return;
  const body = await res.json().catch(() => ({ detail: res.statusText }));
  const detail = typeof body?.detail === "string" ? body.detail : undefined;
  throw new AssessmentsApiError(
    res.status,
    detail ?? `assessments API error ${res.status}`,
    detail,
  );
}

/* -------------------------------------------------------------------------
 * Public surface — four typed functions consumed by the dashboard pages.
 * ------------------------------------------------------------------------- */

export async function listPendingAssessments(): Promise<PendingAssessment[]> {
  const res = await _fetchWithTimeout("/api/admin/assessments/pending", {
    method: "GET",
  });
  await _throwOnError(res);
  return (await res.json()) as PendingAssessment[];
}

export async function getAssessmentVersion(
  versionId: number,
): Promise<AssessmentVersion> {
  const res = await _fetchWithTimeout(
    `/api/admin/assessments/${versionId}`,
    { method: "GET" },
  );
  await _throwOnError(res);
  return (await res.json()) as AssessmentVersion;
}

export async function reviewAssessment(
  versionId: number,
  action: ReviewAction,
  comment: string | null,
): Promise<ReviewResponse> {
  const res = await _fetchWithTimeout(
    `/api/admin/assessments/${versionId}/review`,
    {
      method: "POST",
      body: JSON.stringify({ action, comment }),
    },
  );
  await _throwOnError(res);
  return (await res.json()) as ReviewResponse;
}

export async function publishAssessment(
  versionId: number,
): Promise<PublishResponse> {
  const res = await _fetchWithTimeout(
    `/api/admin/assessments/${versionId}/publish`,
    { method: "POST" },
  );
  await _throwOnError(res);
  return (await res.json()) as PublishResponse;
}
