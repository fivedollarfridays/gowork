"use client";

import Link from "next/link";
import {
  TranslationProvider,
  useTranslation,
} from "@/hooks/useTranslation";
import { EdgeStateShell } from "@/components/edge-states/EdgeStateShell";

/**
 * polish-2 T38 — Branded 404 page (Driver D).
 *
 * The 404 was originally introduced in T13.x; W1 (T1.40) ported it onto
 * the wall metaphor with i18n copy from `edge.404.*`. Polish-2 lifts the
 * Ch1 hero atmosphere (grid + dual glow + grain) onto the page through
 * `EdgeStateShell` so the failure state feels like the same site, not a
 * dead-end.
 *
 * Single CTA back home. EN + ES parity is enforced by the W1 translation
 * gate (the same `edge.404.*` keys are read in both locales). Renders a
 * `main#main` landmark via the shell so the root layout's SkipToContent
 * link still has a target.
 */
function NotFoundContent(): JSX.Element {
  const { t } = useTranslation();
  return (
    <EdgeStateShell
      kind="404"
      eyebrow="404"
      accent="cyan"
      headline={t("edge.404.title")}
      body={t("edge.404.body")}
      cta={
        <Link
          href="/"
          className="inline-flex items-center justify-center gap-2 rounded-full bg-cyan-400 px-6 py-3 text-sm font-semibold text-slate-900 transition hover:bg-cyan-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
        >
          {t("edge.404.cta")}
          <span aria-hidden="true">→</span>
        </Link>
      }
    />
  );
}

export default function NotFound(): JSX.Element {
  return (
    <TranslationProvider>
      <NotFoundContent />
    </TranslationProvider>
  );
}
