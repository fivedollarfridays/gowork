"use client";

import { useEffect } from "react";
import {
  TranslationProvider,
  useTranslation,
} from "@/hooks/useTranslation";

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

/**
 * T1.41 — Branded 500 error page.
 *
 * The dispatch locks the motif : "Something stalled. We're calibrating."
 * Copy comes from the i18n catalog (edge.500.*) so EN + ES parity is
 * enforced by the W1 translation gate. The error message and stack
 * trace are NEVER rendered to end users (judges and Carlos see a clean,
 * branded page, not raw exception text). The digest is logged for dev
 * visibility only.
 *
 * Renders a `main#main` landmark so SkipToContent still works on errors.
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
    <main
      id="main"
      role="main"
      className="mx-auto flex min-h-[70vh] w-full max-w-2xl flex-col items-center justify-center gap-6 px-4 py-12 text-center sm:py-20"
      data-edge-state="500"
    >
      <div
        aria-hidden="true"
        className="flex h-20 w-20 items-center justify-center rounded-full bg-destructive/10 text-4xl sm:h-24 sm:w-24 sm:text-5xl"
      >
        <span role="img" aria-label="">
          {"⚠️"}
        </span>
      </div>

      <div className="space-y-3">
        <p className="text-sm font-semibold uppercase tracking-widest text-accent">
          500
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-primary sm:text-4xl">
          {t("edge.500.title")}
        </h1>
        <p className="mx-auto max-w-md text-base text-muted-foreground sm:text-lg">
          {t("edge.500.body")}
        </p>
      </div>

      <div className="flex w-full flex-col items-stretch gap-3 sm:w-auto sm:flex-row sm:items-center">
        <button
          type="button"
          onClick={() => reset()}
          className="inline-flex items-center justify-center gap-2 rounded-full bg-cyan-400 px-6 py-3 text-sm font-semibold text-slate-900 transition hover:bg-cyan-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
        >
          {t("edge.500.cta")}
        </button>
      </div>
    </main>
  );
}

export default function ErrorPage(props: ErrorPageProps) {
  return (
    <TranslationProvider>
      <ErrorContent {...props} />
    </TranslationProvider>
  );
}
