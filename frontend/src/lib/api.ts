import type {
  AssessmentRequest,
  AssessmentResponse,
  CareerCenterPackage,
  CreditAssessmentResult,
  CreditProfileRequest,
  JobsResponse,
  PlanNarrative,
  PlanResponse,
  ResourceFeedbackRequest,
  ResourceFeedbackResponse,
  TokenValidation,
  VisitFeedbackRequest,
  VisitFeedbackResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function tokenQs(token?: string): string {
  return token ? `?token=${encodeURIComponent(token)}` : "";
}

async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const headers: HeadersInit = { ...init?.headers };
  if (init?.body) {
    (headers as Record<string, string>)["Content-Type"] = "application/json";
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30_000);
  try {
    const res = await fetch(`${API_BASE}${url}`, {
      ...init,
      headers,
      signal: init?.signal ?? controller.signal,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail || `API error ${res.status}`);
    }
    return res.json() as Promise<T>;
  } finally {
    clearTimeout(timeout);
  }
}

export function postAssessment(data: AssessmentRequest): Promise<AssessmentResponse> {
  return apiFetch("/api/assessment/", { method: "POST", body: JSON.stringify(data) });
}

export function getPlan(sessionId: string, token?: string): Promise<PlanResponse> {
  return apiFetch(`/api/plan/${sessionId}${tokenQs(token)}`);
}

export function generateNarrative(sessionId: string, token?: string): Promise<PlanNarrative> {
  return apiFetch(`/api/plan/${sessionId}/generate${tokenQs(token)}`, { method: "POST" });
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

export function submitResourceFeedback(data: ResourceFeedbackRequest): Promise<ResourceFeedbackResponse> {
  return apiFetch("/api/feedback/resource", { method: "POST", body: JSON.stringify(data) });
}

export function validateFeedbackToken(token: string): Promise<TokenValidation> {
  return apiFetch(`/api/feedback/validate/${encodeURIComponent(token)}`);
}

export function submitVisitFeedback(data: VisitFeedbackRequest): Promise<VisitFeedbackResponse> {
  return apiFetch("/api/feedback/visit", { method: "POST", body: JSON.stringify(data) });
}

export function getCareerCenterPackage(sessionId: string, token?: string): Promise<CareerCenterPackage> {
  return apiFetch(`/api/plan/${sessionId}/career-center${tokenQs(token)}`);
}
