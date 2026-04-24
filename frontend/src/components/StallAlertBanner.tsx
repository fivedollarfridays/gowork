"use client";

import { useState } from "react";
import Link from "next/link";
import { AlertTriangle, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTranslation } from "@/hooks/useTranslation";

/**
 * Stall severity as produced by the T12.18 stall detector on the backend
 * (`app.modules.common.temporal_types.StallLevel`). The banner renders ONLY
 * on "hard" per T12.30 AC; all other values keep the banner hidden.
 */
export type StallLevel = "none" | "soft" | "medium" | "hard";

/** localStorage key for the 24h dismiss timestamp. ISO 8601 string. */
export const STALL_BANNER_DISMISS_KEY = "stall_banner_dismissed_at";

/** Dismiss TTL — banner re-appears 24h after the user dismisses it. */
export const STALL_BANNER_TTL_MS = 24 * 60 * 60 * 1000;

interface StallAlertBannerProps {
  /** Severity from the backend stall detector. Only "hard" renders the banner. */
  stallLevel: StallLevel;
  /** Optional deep-link override for the navigator CTA; defaults to /plan. */
  ctaHref?: string;
}

function readDismissedAt(): number | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STALL_BANNER_DISMISS_KEY);
    if (!raw) return null;
    const ts = Date.parse(raw);
    return Number.isNaN(ts) ? null : ts;
  } catch {
    return null;
  }
}

function writeDismissedAt(isoString: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STALL_BANNER_DISMISS_KEY, isoString);
  } catch {
    /* ignore quota / private-mode errors */
  }
}

/**
 * Site-wide banner shown at the top of every page when the active session is
 * in HARD stall. Dismiss persists for 24h via localStorage so we don't nag
 * workers who are already aware.
 */
export function StallAlertBanner({
  stallLevel,
  ctaHref = "/plan",
}: StallAlertBannerProps) {
  const { t } = useTranslation();
  // Lazy-init from storage so SSR renders null and the client render picks up
  // the persisted dismiss (state.md notes: useState initializer runs once).
  const [dismissedAt, setDismissedAt] = useState<number | null>(() =>
    readDismissedAt(),
  );

  if (stallLevel !== "hard") return null;

  const now = Date.now();
  if (dismissedAt !== null && now - dismissedAt < STALL_BANNER_TTL_MS) {
    return null;
  }

  function handleDismiss(): void {
    const iso = new Date().toISOString();
    writeDismissedAt(iso);
    setDismissedAt(Date.parse(iso));
  }

  return (
    <div
      role="alert"
      className="border-b border-warning bg-warning/10 px-4 py-3 text-warning-foreground sm:px-8"
    >
      <div className="mx-auto flex max-w-5xl items-start gap-3">
        <AlertTriangle
          className="mt-0.5 h-4 w-4 shrink-0"
          aria-hidden="true"
        />
        <div className="flex-1 space-y-1">
          <p className="text-sm font-semibold">{t("banner.stallTitle")}</p>
          <p className="text-sm">{t("banner.stallBody")}</p>
          <Link
            href={ctaHref}
            className="inline-flex items-center text-sm font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {t("banner.stallCta")}
          </Link>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="shrink-0"
          onClick={handleDismiss}
          aria-label={t("banner.dismissLabel")}
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </Button>
      </div>
    </div>
  );
}
