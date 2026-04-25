"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { TranslationProvider, useTranslation } from "@/hooks/useTranslation";

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

function ErrorContent({ error, reset }: ErrorPageProps) {
  const { t } = useTranslation();

  // Log to the browser console for dev visibility. We deliberately do NOT
  // surface error.message or error.stack in the rendered UI — judges and
  // end users should see a clean, branded page, not raw exception text.
  useEffect(() => {
    if (typeof console !== "undefined") {
      // eslint-disable-next-line no-console
      console.error("[error.tsx] runtime error", {
        digest: error.digest,
      });
    }
  }, [error]);

  return (
    <main className="mx-auto flex min-h-[70vh] w-full max-w-2xl flex-col items-center justify-center gap-6 px-4 py-12 text-center sm:py-20">
      <div
        aria-hidden="true"
        className="flex h-20 w-20 items-center justify-center rounded-full bg-destructive/10 text-4xl sm:h-24 sm:w-24 sm:text-5xl"
      >
        <span role="img" aria-label="">
          {"⚠️"}
        </span>
      </div>

      <div className="space-y-3">
        <p className="text-sm font-semibold uppercase tracking-widest text-destructive">
          500
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-primary sm:text-4xl">
          {t("errors.500.title")}
        </h1>
        <p className="mx-auto max-w-md text-base text-muted-foreground sm:text-lg">
          {t("errors.500.body")}
        </p>
      </div>

      <div className="flex w-full flex-col items-stretch gap-3 sm:w-auto sm:flex-row sm:items-center">
        <Button size="lg" onClick={() => reset()}>
          {t("errors.500.cta_retry")}
        </Button>
        <Button size="lg" variant="outline" asChild>
          <Link href="/">{t("errors.500.cta_home")}</Link>
        </Button>
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
