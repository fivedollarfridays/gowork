import type {
  AssessmentRequest,
  AssessmentResponse,
  CreditAssessmentResult,
  CreditProfileRequest,
  JobsResponse,
  PlanNarrative,
  PlanResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `API error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function postAssessment(data: AssessmentRequest): Promise<AssessmentResponse> {
  return apiFetch("/api/assessment/", { method: "POST", body: JSON.stringify(data) });
}

export function getPlan(sessionId: string): Promise<PlanResponse> {
  return apiFetch(`/api/plan/${sessionId}`);
}

export function generateNarrative(sessionId: string): Promise<PlanNarrative> {
  return apiFetch(`/api/plan/${sessionId}/generate`, { method: "POST" });
}

export function getJobs(params?: {
  barriers?: string;
  transit_accessible?: boolean;
  industry?: string;
}): Promise<JobsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.barriers) searchParams.set("barriers", params.barriers);
  if (params?.transit_accessible != null) searchParams.set("transit_accessible", String(params.transit_accessible));
  if (params?.industry) searchParams.set("industry", params.industry);
  const qs = searchParams.toString();
  return apiFetch(`/api/jobs/${qs ? `?${qs}` : ""}`);
}

export function postCredit(data: CreditProfileRequest): Promise<CreditAssessmentResult> {
  return apiFetch("/api/credit/assess", { method: "POST", body: JSON.stringify(data) });
}
