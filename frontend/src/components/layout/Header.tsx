"use client";

import Link from "next/link";
import { Suspense } from "react";
import { NavBar } from "@/components/NavBar";
import { StallAlertBannerMount } from "@/components/layout/StallAlertBannerMount";
import { TranslationProvider } from "@/hooks/useTranslation";

/**
 * Site-wide header. Renders the primary nav (NavBar) on every page and the
 * site-wide stall alert banner when the active session is HARD-stalled.
 *
 * Wrapped in TranslationProvider so the header renders correctly even on
 * pages that don't mount their own provider.
 */
export function Header() {
  return (
    <Suspense fallback={null}>
      <TranslationProvider>
        <StallAlertBannerMount />
        <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4 sm:px-8">
            <Link href="/" className="flex items-center gap-2">
              <span className="text-2xl font-extrabold tracking-tight text-primary drop-shadow-[0_0_12px_rgba(255,255,255,0.7)]">
                MontGoWork
              </span>
            </Link>
            <NavBar />
          </div>
        </header>
      </TranslationProvider>
    </Suspense>
  );
}
