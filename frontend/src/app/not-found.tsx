"use client";

import Link from "next/link";
import {
  TranslationProvider,
  useTranslation,
} from "@/hooks/useTranslation";

/**
 * T1.40 — Branded 404 page.
 *
 * Per the design plan, the 404 is "where premium-feel sites lose their
 * premium feel" and the dispatch — ours doesn't. The copy carries the
 * wall metaphor through the failure state ("There is no path to this URL
 * — but there is one through the wall"), drawn from the i18n catalog
 * (edge.404.*) so EN + ES parity is enforced by the W1 translation gate.
 *
 * Renders a `main#main` landmark so the SkipToContent link in the root
 * layout still has a valid target on the 404 page. The CTA links back to
 * the wall (the home view).
 */
function NotFoundContent(): JSX.Element {
  const { t } = useTranslation();
  return (
    <main
      id="main"
      role="main"
      className="mx-auto flex min-h-[70vh] w-full max-w-2xl flex-col items-center justify-center gap-6 px-4 py-12 text-center sm:py-20"
      data-edge-state="404"
    >
      <div
        aria-hidden="true"
        className="flex h-20 w-20 items-center justify-center rounded-full bg-secondary/10 text-4xl sm:h-24 sm:w-24 sm:text-5xl"
      >
        <span role="img" aria-label="">
          {"🧭"}
        </span>
      </div>

      <div className="space-y-3">
        <p className="text-sm font-semibold uppercase tracking-widest text-cyan-400">
          404
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-primary sm:text-4xl">
          {t("edge.404.title")}
        </h1>
        <p className="mx-auto max-w-md text-base text-muted-foreground sm:text-lg">
          {t("edge.404.body")}
        </p>
      </div>

      <div className="flex w-full flex-col items-stretch gap-3 sm:w-auto sm:flex-row sm:items-center">
        <Link
          href="/"
          className="inline-flex items-center justify-center gap-2 rounded-full bg-cyan-400 px-6 py-3 text-sm font-semibold text-slate-900 transition hover:bg-cyan-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
        >
          {t("edge.404.cta")}
          <span aria-hidden="true">→</span>
        </Link>
      </div>
    </main>
  );
}

export default function NotFound(): JSX.Element {
  return (
    <TranslationProvider>
      <NotFoundContent />
    </TranslationProvider>
  );
}
