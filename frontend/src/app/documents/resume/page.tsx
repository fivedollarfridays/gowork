"use client";

import { Suspense, useCallback, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { TranslationProvider, useTranslation } from "@/hooks/useTranslation";
import { useSessionId, useToken } from "@/app/plan/hooks";
import {
  type DocumentVersion,
  generateResume,
  getResumeMarkdown,
} from "@/lib/api/documents";
import { DocumentPreview } from "@/components/documents/DocumentPreview";
import { VersionHistoryList } from "@/components/documents/VersionHistoryList";
import { useDocumentsData } from "../_lib/useDocumentsData";

function ResumeContent() {
  const { t } = useTranslation();
  const { id: sessionId, ready: sessionReady } = useSessionId();
  const { token, ready: tokenReady } = useToken(sessionId);

  const [targetJob, setTargetJob] = useState("");
  const [preview, setPreview] = useState<string | null>(null);

  const { versions, isLoading, invalidate } = useDocumentsData(
    sessionId,
    token,
  );

  const generateMut = useMutation({
    mutationFn: async () => {
      const body = targetJob.trim()
        ? { session_id: sessionId!, job_description: targetJob.trim() }
        : { session_id: sessionId! };
      const created = await generateResume(body, token!);
      const md = await getResumeMarkdown(created.version_id, token!);
      return md;
    },
    onSuccess: (md) => {
      setPreview(md);
      invalidate();
    },
  });

  const handleView = useCallback(
    async (version: DocumentVersion) => {
      if (!token) return;
      try {
        const md = await getResumeMarkdown(version.version_id, token);
        setPreview(md);
      } catch {
        // preview failure is non-fatal; the user can still download the PDF.
      }
    },
    [token],
  );

  if (!sessionReady || !tokenReady) {
    return (
      <main className="min-h-screen px-4 py-8 sm:px-8">
        <p className="text-muted-foreground">{t("documents.loading")}</p>
      </main>
    );
  }

  if (!sessionId || !token) {
    return (
      <main className="min-h-screen px-4 py-8 sm:px-8">
        <div className="mx-auto max-w-4xl">
          <h1 className="text-3xl font-bold text-primary">
            {t("documents.resumeTitle")}
          </h1>
          <p className="mt-4 text-muted-foreground">
            {t("documents.missingSession")}
          </p>
        </div>
      </main>
    );
  }

  const generating = generateMut.isPending;
  const generateFailed = generateMut.isError;

  return (
    <main className="min-h-screen px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <header>
          <h1 className="text-3xl font-bold text-primary">
            {t("documents.resumeTitle")}
          </h1>
          <p className="text-muted-foreground">
            {t("documents.resumeSubtitle")}
          </p>
        </header>

        <section className="space-y-3 rounded-md border border-border p-4">
          <label
            htmlFor="resume-target-job"
            className="block text-sm font-medium"
          >
            {t("documents.targetJobLabel")}
          </label>
          <textarea
            id="resume-target-job"
            aria-label={t("documents.targetJobLabel")}
            placeholder={t("documents.targetJobPlaceholder")}
            value={targetJob}
            onChange={(e) => setTargetJob(e.target.value)}
            rows={5}
            className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          />
          <div className="flex flex-wrap items-center gap-3">
            <Button
              type="button"
              onClick={() => generateMut.mutate()}
              disabled={generating}
            >
              {generating
                ? t("documents.generating")
                : t("documents.generateResume")}
            </Button>
            {generateFailed && (
              <p role="alert" className="text-sm text-destructive">
                {t("documents.generateError")}
              </p>
            )}
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-semibold">
            {t("documents.previewHeading")}
          </h2>
          <DocumentPreview
            markdown={preview}
            emptyText={t("documents.previewEmpty")}
            ariaLabel={t("documents.previewLabel")}
          />
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-semibold">
            {t("documents.historyHeading")}
          </h2>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">
              {t("documents.loading")}
            </p>
          ) : (
            <VersionHistoryList
              versions={versions}
              token={token}
              docType="resume"
              emptyText={t("documents.historyEmptyResume")}
              viewLabel={t("documents.historyView")}
              pdfLabel={t("documents.historyDownloadPdf")}
              generationBadgeLabels={{
                template: t("documents.badgeTemplate"),
                llm: t("documents.badgeLlm"),
              }}
              onView={handleView}
            />
          )}
        </section>
      </div>
    </main>
  );
}

export default function ResumePage() {
  return (
    <Suspense fallback={null}>
      <TranslationProvider>
        <ResumeContent />
      </TranslationProvider>
    </Suspense>
  );
}
