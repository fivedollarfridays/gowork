"use client";

import { useState, useCallback } from "react";
import { Share2, Check, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { createShareLink } from "@/lib/api";

interface Props {
  sessionId: string;
  token: string;
}

export function SharePlanButton({ sessionId, token }: Props) {
  const [state, setState] = useState<"idle" | "loading" | "copied" | "error">("idle");

  const handleShare = useCallback(async () => {
    setState("loading");
    try {
      const result = await createShareLink(sessionId, token);
      const fullUrl = `${window.location.origin}${result.url}`;
      await navigator.clipboard.writeText(fullUrl);
      setState("copied");
      setTimeout(() => setState("idle"), 3000);
    } catch {
      setState("error");
      setTimeout(() => setState("idle"), 3000);
    }
  }, [sessionId, token]);

  const label =
    state === "loading" ? "Sharing..." :
    state === "copied" ? "Copied!" :
    state === "error" ? "Failed" :
    "Share Plan";

  const icon =
    state === "loading" ? <Loader2 className="h-4 w-4 animate-spin" /> :
    state === "copied" ? <Check className="h-4 w-4" /> :
    <Share2 className="h-4 w-4" />;

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleShare}
      disabled={state === "loading"}
      className={state === "copied" ? "text-success border-success/30" : ""}
    >
      {icon}
      <span className="ml-1.5">{label}</span>
    </Button>
  );
}
