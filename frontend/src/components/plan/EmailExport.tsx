"use client";

import { useState } from "react";
import { Mail, Loader2, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function isEmailJSConfigured(): boolean {
  return (
    typeof window !== "undefined" &&
    !!process.env.NEXT_PUBLIC_EMAILJS_SERVICE_ID &&
    !!process.env.NEXT_PUBLIC_EMAILJS_TEMPLATE_ID &&
    !!process.env.NEXT_PUBLIC_EMAILJS_PUBLIC_KEY
  );
}

function buildPlanUrl(sessionId: string, token: string): string {
  const base = typeof window !== "undefined" ? window.location.origin : "";
  return `${base}/plan?session=${encodeURIComponent(sessionId)}&token=${encodeURIComponent(token)}`;
}

function buildTemplateParams(
  toEmail: string,
  sessionId: string,
  token: string,
): Record<string, string> {
  return {
    to_email: toEmail,
    plan_url: buildPlanUrl(sessionId, token),
    summary: "Your MontGoWork employment plan is ready. Use the link below to view your full plan.",
  };
}

interface EmailExportProps {
  sessionId: string;
  token?: string;
}

export function EmailExport({ sessionId, token }: EmailExportProps) {
  const [showForm, setShowForm] = useState(false);
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  if (!isEmailJSConfigured()) return null;

  async function handleSend() {
    setError(null);

    if (!EMAIL_REGEX.test(email)) {
      setError("Please enter a valid email address.");
      return;
    }

    setSending(true);
    try {
      const emailjs = (await import("@emailjs/browser")).default;
      const params = buildTemplateParams(email, sessionId, token ?? "");
      await emailjs.send(
        process.env.NEXT_PUBLIC_EMAILJS_SERVICE_ID!,
        process.env.NEXT_PUBLIC_EMAILJS_TEMPLATE_ID!,
        params,
        process.env.NEXT_PUBLIC_EMAILJS_PUBLIC_KEY!,
      );
      setSent(true);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to send email.";
      setError(msg);
    } finally {
      setSending(false);
    }
  }

  if (sent) {
    return (
      <div aria-live="polite" className="flex items-center gap-2 text-sm text-success">
        <CheckCircle className="h-4 w-4" />
        <span>Plan sent to {email}</span>
      </div>
    );
  }

  if (!showForm) {
    return (
      <Button
        variant="outline"
        size="sm"
        className="gap-2"
        onClick={() => setShowForm(true)}
      >
        <Mail className="h-4 w-4" />
        Email My Plan
      </Button>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Input
        type="email"
        placeholder="your@email.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="w-56"
        onKeyDown={(e) => {
          if (e.key === "Enter") handleSend();
        }}
      />
      <Button
        size="sm"
        disabled={sending}
        onClick={handleSend}
      >
        {sending ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin mr-1" />
            Sending
          </>
        ) : (
          "Send"
        )}
      </Button>
      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
    </div>
  );
}
