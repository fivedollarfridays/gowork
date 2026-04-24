"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { type DocumentVersion, type JobMatchRef } from "@/lib/api/documents";

export interface CoverLetterFormValues {
  resumeVersionId: number;
  jobMatch: JobMatchRef;
}

export interface CoverLetterFormLabels {
  resumeVersionLabel: string;
  resumeVersionEmpty: string;
  jobTitleLabel: string;
  jobCompanyLabel: string;
  jobDescriptionLabel: string;
  submitLabel: string;
  submittingLabel: string;
  errorLabel: string;
}

export interface CoverLetterFormProps {
  resumes: DocumentVersion[];
  submitting: boolean;
  failed: boolean;
  labels: CoverLetterFormLabels;
  onSubmit: (values: CoverLetterFormValues) => void;
}

/**
 * Cover-letter generation form. The generate button is disabled when
 * there are no resume versions (user must generate a resume first) or
 * when the required fields aren't filled.
 */
export function CoverLetterForm({
  resumes,
  submitting,
  failed,
  labels,
  onSubmit,
}: CoverLetterFormProps) {
  const [resumeVersionId, setResumeVersionId] = useState<number | null>(
    resumes[0]?.version_id ?? null,
  );
  const [jobTitle, setJobTitle] = useState("");
  const [company, setCompany] = useState("");
  const [jobDescription, setJobDescription] = useState("");

  // If resumes appear after mount, default to the newest one.
  useEffect(() => {
    if (resumeVersionId == null && resumes.length > 0) {
      setResumeVersionId(resumes[0].version_id);
    }
  }, [resumes, resumeVersionId]);

  const hasResume = resumes.length > 0;
  const disabled =
    submitting ||
    !hasResume ||
    resumeVersionId == null ||
    !jobTitle.trim() ||
    !company.trim();

  function handleSubmit() {
    if (disabled || resumeVersionId == null) return;
    onSubmit({
      resumeVersionId,
      jobMatch: {
        title: jobTitle.trim(),
        company: company.trim(),
        description: jobDescription.trim() || undefined,
      },
    });
  }

  return (
    <div className="space-y-3 rounded-md border border-border p-4">
      {!hasResume && (
        <p role="alert" className="text-sm text-destructive">
          {labels.resumeVersionEmpty}
        </p>
      )}

      <div>
        <label
          htmlFor="cover-letter-resume"
          className="block text-sm font-medium"
        >
          {labels.resumeVersionLabel}
        </label>
        <select
          id="cover-letter-resume"
          aria-label={labels.resumeVersionLabel}
          className="mt-1 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
          value={resumeVersionId ?? ""}
          onChange={(e) => setResumeVersionId(Number(e.target.value))}
          disabled={!hasResume}
        >
          {resumes.map((r) => (
            <option key={r.version_id} value={r.version_id}>
              v{r.version_counter} — {new Date(r.created_at).toLocaleDateString()}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="cover-letter-title" className="block text-sm font-medium">
          {labels.jobTitleLabel}
        </label>
        <Input
          id="cover-letter-title"
          aria-label={labels.jobTitleLabel}
          value={jobTitle}
          onChange={(e) => setJobTitle(e.target.value)}
        />
      </div>

      <div>
        <label
          htmlFor="cover-letter-company"
          className="block text-sm font-medium"
        >
          {labels.jobCompanyLabel}
        </label>
        <Input
          id="cover-letter-company"
          aria-label={labels.jobCompanyLabel}
          value={company}
          onChange={(e) => setCompany(e.target.value)}
        />
      </div>

      <div>
        <label
          htmlFor="cover-letter-description"
          className="block text-sm font-medium"
        >
          {labels.jobDescriptionLabel}
        </label>
        <textarea
          id="cover-letter-description"
          aria-label={labels.jobDescriptionLabel}
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          rows={4}
          className="mt-1 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm"
        />
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Button type="button" onClick={handleSubmit} disabled={disabled}>
          {submitting ? labels.submittingLabel : labels.submitLabel}
        </Button>
        {failed && (
          <p role="alert" className="text-sm text-destructive">
            {labels.errorLabel}
          </p>
        )}
      </div>
    </div>
  );
}
