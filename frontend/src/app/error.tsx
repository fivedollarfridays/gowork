"use client";

import { useEffect } from "react";
import {
  TranslationProvider,
  useTranslation,
} from "@/hooks/useTranslation";
import { EdgeStateShell } from "@/components/edge-states/EdgeStateShell";

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

/**
 * polish-2 T39 — Branded 500 error page (Driver D).
 *
 * Lifts the wall metaphor + Ch1 atmosphere onto the failure state via
 * `EdgeStateShell`. Copy comes from the i18n catalog (`edge.500.*`) so
 * EN + ES parity is enforced by the W1 translation gate. The error
 * message and stack trace are NEVER rendered to end users — only the
 * digest is logged for dev visibility. The retry button calls Next 13's
 * `reset()` prop directly.
 */
function ErrorContent({ error, reset }: ErrorPageProps) {
  const { t } = useTranslation();

  useEffect(() => {
    if (typeof console !== "undefined") {
      // eslint-disable-next-line no-console
      console.error("[error.tsx] runtime error", { digest: error.digest });
    }
  }, [error]);

  return (
    <EdgeStateShell
      kind="500"
      eyebrow="500"
      accent="rose"
      headline={t("edge.500.title")}
      body={t("edge.500.body")}
      cta={
        <button
          type="button"
          onClick={() => reset()}
          className="inline-flex items-center justify-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        >
          {t("edge.500.cta")}
        </button>
      }
    />
  );
}

export default function ErrorPage(props: ErrorPageProps) {
  return (
    <TranslationProvider>
      <ErrorContent {...props} />
    </TranslationProvider>
  );
}
