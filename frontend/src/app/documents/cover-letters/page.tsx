"use client";

import { Suspense, useCallback, useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { TranslationProvider, useTranslation } from "@/hooks/useTranslation";
import { useSessionId, useToken } from "@/app/plan/hooks";
import {
  type DocumentVersion,
  type JobMatchRef,
  generateCoverLetter,
  getCoverLetterMarkdown,
} from "@/lib/api/documents";
import { DocumentPreview } from "@/components/documents/DocumentPreview";
import { VersionHistoryList } from "@/components/documents/VersionHistoryList";
import {
  CoverLetterForm,
  type CoverLetterFormValues,
} from "@/components/documents/CoverLetterForm";
import { useDocumentsData } from "../_lib/useDocumentsData";

function CoverLettersContent() {
  const { t } = useTranslation();
  const { id: sessionId, ready: sessionReady } = useSessionId();
  const { token, ready: tokenReady } = useToken(sessionId);

  const [preview, setPreview] = useState<string | null>(null);

  const { versions, isLoading, invalidate } = useDocumentsData(
    sessionId,
    token,
  );

  const resumes = useMemo(
    () => versions.filter((v) => v.doc_type === "resume"),
    [versions],
  );

  const generateMut = useMutation({
    mutationFn: async (payload: {
      resume_version_id: number;
      job_match_ref: JobMatchRef;
    }) => {
      const created = await generateCoverLetter(
        { session_id: sessionId!, ...payload },
        token!,
      );
      const md = await getCoverLetterMarkdown(created.version_id, token!);
      return md;
    },
    onSuccess: (md) => {
      setPreview(md);
      invalidate();
    },
  });

  const handleSubmit = useCallback(
    (values: CoverLetterFormValues) => {
      generateMut.mutate({
        resume_version_id: values.resumeVersionId,
        job_match_ref: values.jobMatch,
      });
    },
    [generateMut],
  );

  const handleView = useCallback(
    async (version: DocumentVersion) => {
      if (!token) return;
      try {
        const md = await getCoverLetterMarkdown(version.version_id, token);
        setPreview(md);
      } catch {
        // preview failure non-fatal; PDF download still works.
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
            {t("documents.coverLetterTitle")}
          </h1>
          <p className="mt-4 text-muted-foreground">
            {t("documents.missingSession")}
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <header>
          <h1 className="text-3xl font-bold text-primary">
            {t("documents.coverLetterTitle")}
          </h1>
          <p className="text-muted-foreground">
            {t("documents.coverLetterSubtitle")}
          </p>
        </header>

        <CoverLetterForm
          resumes={resumes}
          submitting={generateMut.isPending}
          failed={generateMut.isError}
          labels={{
            resumeVersionLabel: t("documents.resumeVersionLabel"),
            resumeVersionEmpty: t("documents.resumeVersionEmpty"),
            jobTitleLabel: t("documents.jobTitleLabel"),
            jobCompanyLabel: t("documents.jobCompanyLabel"),
            jobDescriptionLabel: t("documents.jobDescriptionLabel"),
            submitLabel: t("documents.generateCoverLetter"),
            submittingLabel: t("documents.generating"),
            errorLabel: t("documents.generateCoverError"),
          }}
          onSubmit={handleSubmit}
        />

        <section className="space-y-3">
          <h2 className="text-xl font-semibold">
            {t("documents.previewHeading")}
          </h2>
          <DocumentPreview
            markdown={preview}
            emptyText={t("documents.previewEmptyCover")}
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
              docType="cover_letter"
              emptyText={t("documents.historyEmptyCover")}
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

export default function CoverLettersPage() {
  return (
    <Suspense fallback={null}>
      <TranslationProvider>
        <CoverLettersContent />
      </TranslationProvider>
    </Suspense>
  );
}
