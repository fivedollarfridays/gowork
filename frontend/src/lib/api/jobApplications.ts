/**
 * Typed API client for the MontGoWork Job-Applications feature (T12.13).
 *
 * Every endpoint takes a `token` query parameter. The backend verifies it
 * against the session referenced by `session_id`; mismatches return 403.
 * URL layout is intentionally hyphenated (`/api/job-applications`) to
 * avoid collision with the older `/api/jobs/{job_id}` resource.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type JobApplicationStatus =
  | "draft"
  | "applied"
  | "interview"
  | "offer"
  | "rejected"
  | "withdrawn";

export type GenerationMethod = "llm" | "template";

export interface JobApplication {
  id: number;
  session_id: string;
  match_source: string | null;
  match_url: string | null;
  company: string | null;
  role: string | null;
  resume_version_id: number | null;
  status: JobApplicationStatus;
  applied_date: string | null;
  created_at: string | null;
}

export interface FunnelCounts {
  draft: number;
  applied: number;
  interview: number;
  offer: number;
  rejected: number;
  withdrawn: number;
}

export interface FunnelResult {
  counts: FunnelCounts;
  draft_to_applied_rate: number | null;
  applied_to_interview_rate: number | null;
  interview_to_offer_rate: number | null;
}

export interface ResumeVersionInfo {
  version_id: number;
  session_id: string;
  doc_type: string;
  version_counter: number;
  generation_method: GenerationMethod | string | null;
  use_counter: number;
  created_at: string;
}

/** Per-request hard timeout (T13.92). */
const REQUEST_TIMEOUT_MS = 30_000;

/**
 * Compose the caller's signal (if any) with our local timeout signal so
 * that BOTH abort triggers are honoured (T13 stage-2 P1-4). The prior
 * ``init?.signal ?? controller.signal`` silently dropped the timeout
 * whenever the caller supplied their own signal.
 */
function _composeSignal(
  callerSignal: AbortSignal | null | undefined,
  timeoutSignal: AbortSignal,
): AbortSignal {
  if (!callerSignal) return timeoutSignal;
  return AbortSignal.any([callerSignal, timeoutSignal]);
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: HeadersInit = { ...(init?.headers ?? {}) };
  if (init?.body) {
    (headers as Record<string, string>)["Content-Type"] = "application/json";
  }
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers,
      signal: _composeSignal(init?.signal, controller.signal),
    });
    if (!res.ok) {
      const body = await res
        .json()
        .catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail || `API error ${res.status}`);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timeoutId);
  }
}

function qs(params: Record<string, string | number>): string {
  const search = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) search.set(k, String(v));
  return search.toString();
}

export function listApplications(
  sessionId: string,
  token: string,
): Promise<JobApplication[]> {
  return apiFetch(
    `/api/job-applications?${qs({ session_id: sessionId, token })}`,
  );
}

export function updateApplicationStatus(
  id: number,
  status: JobApplicationStatus,
  token: string,
  outcomeDate?: string,
): Promise<JobApplication> {
  const body: Record<string, string> = { status };
  if (outcomeDate) body.outcome_date = outcomeDate;
  return apiFetch(`/api/job-applications/${id}?${qs({ token })}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function getFunnel(
  sessionId: string,
  token: string,
): Promise<FunnelResult> {
  return apiFetch(
    `/api/job-applications/funnel?${qs({
      session_id: sessionId,
      token,
    })}`,
  );
}

export function listResumeVersions(
  sessionId: string,
  token: string,
): Promise<ResumeVersionInfo[]> {
  return apiFetch(
    `/api/documents/versions?${qs({ session_id: sessionId, token })}`,
  );
}
