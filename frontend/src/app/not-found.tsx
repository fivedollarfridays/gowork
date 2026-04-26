"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { TranslationProvider, useTranslation } from "@/hooks/useTranslation";

function NotFoundContent() {
  const { t } = useTranslation();
  return (
    <main className="mx-auto flex min-h-[70vh] w-full max-w-2xl flex-col items-center justify-center gap-6 px-4 py-12 text-center sm:py-20">
      <div
        aria-hidden="true"
        className="flex h-20 w-20 items-center justify-center rounded-full bg-secondary/10 text-4xl sm:h-24 sm:w-24 sm:text-5xl"
      >
        <span role="img" aria-label="">
          {"🧭"}
        </span>
      </div>

      <div className="space-y-3">
        <p className="text-sm font-semibold uppercase tracking-widest text-secondary">
          404
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-primary sm:text-4xl">
          {t("errors.404.title")}
        </h1>
        <p className="mx-auto max-w-md text-base text-muted-foreground sm:text-lg">
          {t("errors.404.body")}
        </p>
      </div>

      <div className="flex w-full flex-col items-stretch gap-3 sm:w-auto sm:flex-row sm:items-center">
        <Button size="lg" asChild>
          <Link href="/">{t("errors.404.cta_home")}</Link>
        </Button>
        <Button size="lg" variant="outline" asChild>
          <Link href="/daily">{t("errors.404.cta_daily")}</Link>
        </Button>
      </div>
    </main>
  );
}

export default function NotFound() {
  return (
    <TranslationProvider>
      <NotFoundContent />
    </TranslationProvider>
  );
}
