import type {
  AssessmentRequest,
  AssessmentResponse,
  CareerCenterPackage,
  ChatMode,
  ChatSSEEvent,
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

export function toggleAction(
  sessionId: string,
  actionKey: string,
  completed: boolean,
  token?: string,
): Promise<{ checklist: Record<string, boolean> }> {
  return apiFetch(`/api/plan/${sessionId}/actions${tokenQs(token)}`, {
    method: "PATCH",
    body: JSON.stringify({ action_key: actionKey, completed }),
  });
}

export function getCareerCenterPackage(sessionId: string, token?: string): Promise<CareerCenterPackage> {
  return apiFetch(`/api/plan/${sessionId}/career-center${tokenQs(token)}`);
}

export async function streamBarrierIntelChat(
  sessionId: string,
  question: string,
  mode: ChatMode,
  onEvent: (event: ChatSSEEvent) => void,
): Promise<void> {
  const token = typeof window !== "undefined" ? sessionStorage.getItem("session_token") ?? "" : "";
  const res = await fetch(`${API_BASE}/api/barrier-intel/chat${tokenQs(token)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, user_question: question, mode }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `API error ${res.status}`);
  }
  // Handle guardrail response (non-streaming JSON)
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    const data = await res.json();
    onEvent({ type: "token", text: data.message });
    onEvent({ type: "done" });
    return;
  }
  // SSE streaming
  const reader = res.body?.getReader();
  if (!reader) return;
  const decoder = new TextDecoder();
  let buffer = "";
  const TIMEOUT_MS = 30_000;
  let timer: ReturnType<typeof setTimeout> | undefined;
  const abortCtrl = new AbortController();

  const resetTimer = () => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      reader.cancel();
      abortCtrl.abort();
    }, TIMEOUT_MS);
  };

  try {
    resetTimer();
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { done, value } = await reader.read();
      if (done || abortCtrl.signal.aborted) break;
      resetTimer();
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const event: ChatSSEEvent = JSON.parse(line.slice(6));
            onEvent(event);
          } catch {
            // Skip malformed SSE data
          }
        }
      }
    }
    if (abortCtrl.signal.aborted) {
      throw new Error("Stream timed out after 30 seconds of inactivity");
    }
  } finally {
    if (timer) clearTimeout(timer);
    reader.releaseLock();
  }
}
