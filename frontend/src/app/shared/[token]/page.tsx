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
    fetch(`${API_BASE}/api/plan/shared/${encodeURIComponent(params.token)}`)
      .then((res) => {
        if (!res.ok) throw new Error("Not found");
        return res.json();
      })
      .then((data) => setPlan(data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
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
