"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { SharedPlanView, type SharedPlanData } from "../SharedPlanView";
import { TranslationProvider } from "@/hooks/useTranslation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SharedPlanPage() {
  const params = useParams<{ token: string }>();
  const [plan, setPlan] = useState<SharedPlanData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!params.token) {
      setLoading(false);
      setError(true);
      return;
    }
    // T13.92 — 30s hard timeout via AbortController.
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30_000);
    // T13 stage-2 P1-5 — guard every setState behind ``aborted`` so we
    // don't update state after the component unmounts (or after the
    // user navigates to a new token while the fetch is still in
    // flight). The cleanup below aborts the controller, which the
    // ``aborted`` checks then observe.
    const isLive = () => !controller.signal.aborted;
    fetch(`${API_BASE}/api/plan/shared/${encodeURIComponent(params.token)}`, {
      signal: controller.signal,
    })
      .then((res) => {
        if (!res.ok) throw new Error("Not found");
        return res.json();
      })
      .then((data) => {
        if (isLive()) setPlan(data);
      })
      .catch(() => {
        if (isLive()) setError(true);
      })
      .finally(() => {
        clearTimeout(timeoutId);
        if (isLive()) setLoading(false);
      });
    return () => {
      clearTimeout(timeoutId);
      controller.abort();
    };
  }, [params.token]);

  if (loading) {
    return (
      <main className="flex items-center justify-center min-h-[60vh]">
        <p className="text-muted-foreground">Loading shared plan...</p>
      </main>
    );
  }

  return (
    <main>
      <TranslationProvider>
        <SharedPlanView plan={error ? null : plan} />
      </TranslationProvider>
    </main>
  );
}
