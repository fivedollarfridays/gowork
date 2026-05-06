"use client";

/**
 * <SaveProgressCTA /> — opt-in account-creation prompt (T22.11).
 *
 * The CTA is rendered at three points in the funnel — post-assessment
 * (/assess), post-plan-generation (/plan), and pre-share (/shared/[token])
 * — to give the worker a low-friction way to claim the anonymous session
 * via a magic-link email. It NEVER gates functionality: anonymous users
 * see and use the same product whether or not they accept the offer.
 *
 * Visibility rules:
 *   1. Hidden when ``useAccount()`` returns a non-null account binding
 *      (the browser is already claimed; no upsell to make).
 *   2. Hidden when the per-page dismissal key in localStorage is
 *      younger than 24 hours — the worker said "not now" and we honor
 *      it for the same browser session and the next day.
 *   3. After 24 hours the dismissal expires and the CTA can re-appear.
 *
 * State machine:
 *   idle    → email form, submit disabled until email is non-empty
 *   pending → button shows spinner
 *   sent    → "check your email" confirmation (rendered for ALL outcomes
 *             — success or rate-limit reject — to mirror the no-enumeration
 *             contract from /auth/login)
 */

import {
  useCallback,
  useEffect,
  useState,
  type FormEvent,
} from "react";
import { useMutation } from "@tanstack/react-query";
import { Loader2, Mail, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { requestMagicLink, useAccount } from "@/lib/api/auth";

const DISMISS_KEY_PREFIX = "gw_save_progress_cta_dismissed_";
const DISMISS_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours

interface SaveProgressCTAProps {
  /**
   * Per-page dismissal scope. Prefer a stable, descriptive name
   * (``"assess"`` / ``"plan"`` / ``"shared"``) so the localStorage
   * key reads naturally during debugging.
   */
  dismissKey: string;
}

function _readDismissedAt(key: string): number | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(DISMISS_KEY_PREFIX + key);
  if (!raw) return null;
  const ts = Number(raw);
  return Number.isFinite(ts) && ts > 0 ? ts : null;
}

function _isFreshlyDismissed(key: string): boolean {
  const ts = _readDismissedAt(key);
  if (ts === null) return false;
  return Date.now() - ts < DISMISS_TTL_MS;
}

export function SaveProgressCTA({ dismissKey }: SaveProgressCTAProps) {
  const account = useAccount();

  // Mirror the dismissal flag into React state so the component re-renders
  // on dismiss without a window event listener. We seed from localStorage
  // on mount so an existing key (set on a prior visit) takes effect.
  const [dismissed, setDismissed] = useState<boolean>(() =>
    _isFreshlyDismissed(dismissKey),
  );

  useEffect(() => {
    setDismissed(_isFreshlyDismissed(dismissKey));
  }, [dismissKey]);

  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const mutation = useMutation({
    mutationFn: (addr: string) => requestMagicLink(addr),
    onSettled: () => setSubmitted(true),
  });

  const handleSubmit = useCallback(
    (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      const trimmed = email.trim();
      if (trimmed.length === 0 || mutation.isPending) return;
      mutation.mutate(trimmed);
    },
    [email, mutation],
  );

  const handleDismiss = useCallback(() => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(
        DISMISS_KEY_PREFIX + dismissKey,
        String(Date.now()),
      );
    }
    setDismissed(true);
  }, [dismissKey]);

  // Already-claimed sessions never see the CTA. We also hide while the
  // ``/api/auth/me`` query is in-flight to avoid the flash-of-CTA that
  // would show for one frame to claimed users.
  if (account.isPending || account.data?.accountId) return null;
  if (dismissed) return null;

  if (submitted) {
    return (
      <Card className="border-secondary/40 bg-secondary/5">
        <CardContent className="pt-6 pb-6 text-center space-y-3">
          <Mail className="mx-auto h-8 w-8 text-primary" aria-hidden />
          <p className="text-base font-semibold">Check your inbox</p>
          <p className="text-sm text-muted-foreground">
            If an account exists for{" "}
            <span className="font-medium">{email.trim()}</span>, we just
            sent a sign-in link. Open it on this device to save your
            progress.
          </p>
        </CardContent>
      </Card>
    );
  }

  const trimmed = email.trim();
  const canSubmit = trimmed.length > 0 && !mutation.isPending;

  return (
    <Card className="border-secondary/40 bg-secondary/5 relative">
      <button
        type="button"
        onClick={handleDismiss}
        aria-label="Dismiss"
        className="absolute top-2 right-2 p-1 text-muted-foreground hover:text-foreground"
      >
        <X className="h-4 w-4" />
      </button>
      <CardContent className="pt-6 pb-5 space-y-4">
        <div className="space-y-1 pr-6">
          <h3 className="text-base font-semibold">Save your progress</h3>
          <p className="text-sm text-muted-foreground">
            Get a one-time link by email so you can come back to your plan
            from any device. No password required.
          </p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-3" noValidate>
          <label htmlFor={`save-cta-email-${dismissKey}`} className="sr-only">
            Email address
          </label>
          <Input
            id={`save-cta-email-${dismissKey}`}
            name="email"
            type="email"
            autoComplete="email"
            inputMode="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={mutation.isPending}
          />
          <Button
            type="submit"
            disabled={!canSubmit}
            className="w-full sm:w-auto min-h-10"
          >
            {mutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Sending...
              </>
            ) : (
              "Save my progress"
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
