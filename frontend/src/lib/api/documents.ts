/**
 * Typed API client for the MontGoWork Documents feature (T12.17).
 *
 * Wraps the seven backend endpoints under ``/api/documents``:
 *  - POST /resume                 (generate resume)
 *  - GET  /resume/{id}            (markdown)
 *  - GET  /resume/{id}/pdf        (PDF bytes)
 *  - POST /cover-letter           (generate cover letter)
 *  - GET  /cover-letter/{id}      (markdown)
 *  - GET  /cover-letter/{id}/pdf  (PDF bytes)
 *  - GET  /versions               (newest-first version history)
 *
 * All endpoints accept a ``token`` query parameter for auth. The backend
 * validates the token against the session referenced by ``session_id``.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type DocType = "resume" | "cover_letter";
export type GenerationMethod = "template" | "llm" | string;

export interface DocumentVersion {
  version_id: number;
  session_id: string;
  doc_type: DocType;
  version_counter: number;
  generation_method: GenerationMethod;
  use_counter: number;
  created_at: string;
}

export interface ResumeCreateBody {
  session_id: string;
  job_description?: string;
}

export interface ResumeCreateResult {
  version_id: number;
  version_counter: number;
  session_id: string;
  doc_type: "resume";
  generation_method: GenerationMethod;
}

export interface JobMatchRef {
  job_id?: string;
  title?: string;
  company?: string;
  location?: string;
  description?: string;
  [key: string]: unknown;
}

export interface CoverLetterCreateBody {
  session_id: string;
  resume_version_id: number;
  job_match_ref: JobMatchRef;
}

export interface CoverLetterCreateResult {
  version_id: number;
  version_counter: number;
  session_id: string;
  doc_type: "cover_letter";
  generation_method: GenerationMethod;
  fair_chance: boolean;
}

function qs(params: Record<string, string | number>): string {
  const search = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) search.set(k, String(v));
  return search.toString();
}

async function readError(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: string };
    return body?.detail || `API error ${res.status}`;
  } catch {
    return `API error ${res.status}`;
  }
}

/** Per-request hard timeout (T13.92). 60s — PDF generation can be slow. */
const REQUEST_TIMEOUT_MS = 60_000;

/**
 * Compose the caller's signal (if any) with our local timeout signal so
 * that BOTH abort triggers are honoured. The previous implementation
 * used ``init?.signal ?? controller.signal`` which silently dropped the
 * timeout whenever the caller passed their own signal — meaning a hung
 * backend call could no longer be terminated by the per-request hard
 * timeout (T13 stage-2 P1-4).
 */
function _composeSignal(
  callerSignal: AbortSignal | null | undefined,
  timeoutSignal: AbortSignal,
): AbortSignal {
  if (!callerSignal) return timeoutSignal;
  return AbortSignal.any([callerSignal, timeoutSignal]);
}

async function _fetchWithTimeout(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    return await fetch(`${API_BASE}${path}`, {
      ...init,
      signal: _composeSignal(init?.signal, controller.signal),
    });
  } finally {
    clearTimeout(timeoutId);
  }
}

async function apiFetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    ...((init?.headers as Record<string, string>) ?? {}),
  };
  if (init?.body) headers["Content-Type"] = "application/json";
  const res = await _fetchWithTimeout(path, { ...init, headers });
  if (!res.ok) throw new Error(await readError(res));
  return (await res.json()) as T;
}

async function apiFetchText(path: string, init?: RequestInit): Promise<string> {
  const res = await _fetchWithTimeout(path, init);
  if (!res.ok) throw new Error(await readError(res));
  return res.text();
}

export function listVersions(
  sessionId: string,
  token: string,
): Promise<DocumentVersion[]> {
  return apiFetchJson<DocumentVersion[]>(
    `/api/documents/versions?${qs({ session_id: sessionId, token })}`,
  );
}

export function generateResume(
  body: ResumeCreateBody,
  token: string,
): Promise<ResumeCreateResult> {
  return apiFetchJson<ResumeCreateResult>(
    `/api/documents/resume?${qs({ token })}`,
    { method: "POST", body: JSON.stringify(body) },
  );
}

export function getResumeMarkdown(
  versionId: number,
  token: string,
): Promise<string> {
  return apiFetchText(
    `/api/documents/resume/${versionId}?${qs({ token })}`,
  );
}

export function resumePdfUrl(versionId: number, token: string): string {
  return `${API_BASE}/api/documents/resume/${versionId}/pdf?${qs({ token })}`;
}

export function generateCoverLetter(
  body: CoverLetterCreateBody,
  token: string,
): Promise<CoverLetterCreateResult> {
  return apiFetchJson<CoverLetterCreateResult>(
    `/api/documents/cover-letter?${qs({ token })}`,
    { method: "POST", body: JSON.stringify(body) },
  );
}

export function getCoverLetterMarkdown(
  versionId: number,
  token: string,
): Promise<string> {
  return apiFetchText(
    `/api/documents/cover-letter/${versionId}?${qs({ token })}`,
  );
}

export function coverLetterPdfUrl(versionId: number, token: string): string {
  return `${API_BASE}/api/documents/cover-letter/${versionId}/pdf?${qs({ token })}`;
}
