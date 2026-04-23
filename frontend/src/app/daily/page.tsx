"use client";

import { Suspense, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { TranslationProvider, useTranslation } from "@/hooks/useTranslation";
import { useSessionId, useToken } from "@/app/plan/hooks";
import {
  parseDigestSections,
  previewDigest,
  type DigestResult,
} from "@/lib/api/digest";
import { DigestYesterdaySection } from "@/components/digest/DigestYesterdaySection";
import { DigestTodaySection } from "@/components/digest/DigestTodaySection";
import { DigestWeekSection } from "@/components/digest/DigestWeekSection";
import { StallAlert } from "@/components/digest/StallAlert";

function isUnauthorized(err: unknown): boolean {
  if (!(err instanceof Error)) return false;
  return /\(401\)|unauthorized/i.test(err.message);
}

function DailyContent() {
  const { t } = useTranslation();
  const { id: sessionId, ready: sessionReady } = useSessionId();
  const { token, ready: tokenReady } = useToken(sessionId);

  const enabled = Boolean(sessionId && token);

  const digestQ = useQuery<DigestResult>({
    queryKey: ["digest", sessionId, token],
    queryFn: () => previewDigest(sessionId!, token!),
    enabled,
  });

  const sections = useMemo(
    () => (digestQ.data ? parseDigestSections(digestQ.data.text) : null),
    [digestQ.data],
  );

  if (!sessionReady || !tokenReady) {
    return (
      <main className="min-h-screen px-4 py-8 sm:px-8">
        <p className="text-muted-foreground">{t("digest.loading")}</p>
      </main>
    );
  }

  if (!sessionId || !token) {
    return (
      <main className="min-h-screen px-4 py-8 sm:px-8">
        <p role="alert" className="text-destructive">
          {t("digest.error.unauthorized")}
        </p>
      </main>
    );
  }

  if (digestQ.isLoading) {
    return (
      <main className="min-h-screen px-4 py-8 sm:px-8">
        <p className="text-muted-foreground">{t("digest.loading")}</p>
      </main>
    );
  }

  if (digestQ.error) {
    const msg = isUnauthorized(digestQ.error)
      ? t("digest.error.unauthorized")
      : t("digest.error.generic");
    return (
      <main className="min-h-screen px-4 py-8 sm:px-8">
        <p role="alert" className="text-destructive">
          {msg}
        </p>
      </main>
    );
  }

  if (!digestQ.data || !sections) {
    return (
      <main className="min-h-screen px-4 py-8 sm:px-8">
        <p className="text-muted-foreground">{t("digest.loading")}</p>
      </main>
    );
  }

  const counts = digestQ.data.section_counts;
  return (
    <main className="min-h-screen px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-3xl space-y-4">
        <header>
          <h1 className="text-2xl font-bold text-primary sm:text-3xl">
            {t("digest.page.title")}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {digestQ.data.subject}
          </p>
        </header>

        {counts.yesterday > 0 && (
          <DigestYesterdaySection
            body={sections.yesterday}
            count={counts.yesterday}
          />
        )}

        {counts.today > 0 && (
          <DigestTodaySection body={sections.today} count={counts.today} />
        )}

        <DigestWeekSection body={sections.week} count={counts.week} />

        {counts.stall > 0 && (
          <StallAlert body={sections.stall} count={counts.stall} />
        )}
      </div>
    </main>
  );
}

export default function DailyPage() {
  return (
    <Suspense fallback={null}>
      <TranslationProvider>
        <DailyContent />
      </TranslationProvider>
    </Suspense>
  );
}
