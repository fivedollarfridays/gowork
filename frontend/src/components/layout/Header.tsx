"use client";

import Link from "next/link";
import { Suspense } from "react";
import { NavBar } from "@/components/NavBar";
import { StallAlertBannerMount } from "@/components/layout/StallAlertBannerMount";
import { TranslationProvider, useTranslation } from "@/hooks/useTranslation";
import { ChapterCounter } from "@/components/wall/ChapterCounter";
import { MuteToggle } from "@/components/wall/MuteToggle";
import { LanguageToggle } from "@/components/wall/LanguageToggle";
import { BrandMark } from "@/components/wall/BrandMark";

/**
 * T1.51 — Header rewrite.
 *
 * The site-wide header is now the GoWork brand surface :
 *   - Brand mark (G + cyan path) top-left, linked back to the wall.
 *   - Persistent NavBar in the middle (worker-companion routes).
 *   - Chapter counter top-right when wallChapter is supplied (Driver
 *     B's chapter-state in W2 will feed this).
 *   - Mute toggle, EN/ES toggle, GitHub icon link.
 *   - StallAlertBannerMount stays mounted above the chrome bar so the
 *     existing T13.6 banner still surfaces on stalled sessions.
 */
const REPO_URL = "https://github.com/fivedollarfridays/montgowork";

export interface HeaderProps {
  /** When set, renders the chapter counter (e.g. 03/10). */
  wallChapter?: { current: number; total: number };
}

function HeaderInner({ wallChapter }: HeaderProps) {
  const { t } = useTranslation();
  return (
    <>
      <StallAlertBannerMount />
      <header className="sticky top-0 z-50 border-b border-foreground/10 bg-background/85 backdrop-blur supports-[backdrop-filter]:bg-background/65">
        <div className="mx-auto flex h-14 max-w-6xl items-center gap-3 px-4 sm:px-8">
          <Link
            href="/"
            aria-label={t("header.brand.label")}
            className="flex items-center gap-2 rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300"
          >
            <BrandMark size={24} />
            <span className="text-lg font-extrabold tracking-tight text-foreground">
              GoWork
            </span>
          </Link>
          <div className="ml-2 hidden sm:block">
            <NavBar />
          </div>
          <div className="ml-auto flex items-center gap-2">
            {wallChapter ? (
              <ChapterCounter
                current={wallChapter.current}
                total={wallChapter.total}
              />
            ) : null}
            <MuteToggle />
            <LanguageToggle />
            <Link
              href={REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={t("header.github.aria")}
              className="inline-flex h-9 w-9 items-center justify-center rounded-full text-foreground/80 transition hover:bg-foreground/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300"
            >
              <GitHubIcon />
            </Link>
          </div>
          <div className="sm:hidden">
            <NavBar />
          </div>
        </div>
      </header>
    </>
  );
}

function GitHubIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      width="18"
      height="18"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M12 0a12 12 0 0 0-3.79 23.4c.6.11.83-.26.83-.58v-2.05c-3.34.73-4.04-1.42-4.04-1.42-.55-1.39-1.34-1.76-1.34-1.76-1.09-.74.08-.73.08-.73 1.21.09 1.85 1.24 1.85 1.24 1.07 1.84 2.81 1.31 3.5 1 .11-.78.42-1.31.76-1.61-2.66-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.13-.3-.54-1.52.12-3.18 0 0 1-.32 3.3 1.23a11.5 11.5 0 0 1 6 0c2.3-1.55 3.3-1.23 3.3-1.23.66 1.66.25 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.81 5.62-5.49 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.22.7.84.58A12 12 0 0 0 12 0z" />
    </svg>
  );
}

export function Header({ wallChapter }: HeaderProps = {}) {
  return (
    <Suspense fallback={null}>
      <TranslationProvider>
        <HeaderInner wallChapter={wallChapter} />
      </TranslationProvider>
    </Suspense>
  );
}
