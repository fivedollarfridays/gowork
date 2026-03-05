import type {
  AssessmentRequest,
  AssessmentResponse,
  CreditAssessmentResult,
  CreditProfileRequest,
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

export function postCredit(data: CreditProfileRequest): Promise<CreditAssessmentResult> {
  return apiFetch("/api/credit/assess", { method: "POST", body: JSON.stringify(data) });
}
