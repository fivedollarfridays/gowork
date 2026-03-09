"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

export function useClientStorage(key: string | null): { value: string | null; ready: boolean } {
  const [state, setState] = useState<{ value: string | null; ready: boolean }>({ value: null, ready: false });
  useEffect(() => {
    if (!key) { setState({ value: null, ready: true }); return; }
    try { setState({ value: sessionStorage.getItem(key), ready: true }); } catch { setState({ value: null, ready: true }); }
  }, [key]);
  return state;
}

export function useSessionId(): { id: string | null; ready: boolean } {
  const searchParams = useSearchParams();
  const fromUrl = searchParams.get("session");
  const stored = useClientStorage(fromUrl ? null : "montgowork_session_id");

  useEffect(() => {
    if (fromUrl) {
      try { sessionStorage.setItem("montgowork_session_id", fromUrl); } catch {}
    }
  }, [fromUrl]);

  if (fromUrl) return { id: fromUrl, ready: true };
  return { id: stored.value, ready: stored.ready };
}

export function useToken(sessionId: string | null): { token: string | null; ready: boolean } {
  const searchParams = useSearchParams();
  const fromUrl = searchParams.get("token");
  const storageKey = (!fromUrl && sessionId) ? `feedback_token_${sessionId}` : null;
  const stored = useClientStorage(storageKey);

  useEffect(() => {
    if (fromUrl && sessionId) {
      try { sessionStorage.setItem(`feedback_token_${sessionId}`, fromUrl); } catch {}
    }
  }, [fromUrl, sessionId]);

  if (fromUrl) return { token: fromUrl, ready: true };
  return { token: stored.value, ready: stored.ready };
}
