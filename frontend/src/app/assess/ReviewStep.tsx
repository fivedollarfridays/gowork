"use client";

import { Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { humanizeLabel } from "@/lib/constants";
import type { BarrierFormData } from "@/components/wizard/BarrierForm";
import type { CreditFormData } from "@/lib/types";

export interface ReviewStepProps {
  formData: BarrierFormData;
  hasResume: boolean;
  resumeWordCount: number;
  creditData: CreditFormData;
  hasCreditBarrier: boolean;
  isPending: boolean;
  error: string | null;
  onWorkHistoryChange: (value: string) => void;
}

export function ReviewStep({
  formData,
  hasResume,
  resumeWordCount,
  creditData,
  hasCreditBarrier,
  isPending,
  error,
  onWorkHistoryChange,
}: ReviewStepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Review & Submit</h2>
        <p className="text-sm text-muted-foreground">
          Add your work history and review your information before submitting.
        </p>
      </div>

      {hasResume ? (
        <div className="rounded-lg border p-4 bg-muted/30 space-y-2">
          <div className="flex justify-between items-center">
            <h3 className="text-sm font-medium">Resume Uploaded</h3>
            <Badge variant="secondary" className="text-xs">
              {resumeWordCount} words extracted
            </Badge>
          </div>
          {!formData.workHistory.trim() ? (
            <p className="text-xs text-muted-foreground">Your resume will be used for job matching.</p>
          ) : (
            <p className="text-xs text-muted-foreground">Your resume and work history will both be used.</p>
          )}
        </div>
      ) : null}

      <div className="space-y-2">
        <label htmlFor="work-history" className="text-sm font-medium">
          Work History {hasResume ? "(optional, resume uploaded)" : ""}
        </label>
        <textarea
          id="work-history"
          value={formData.workHistory}
          onChange={(e) => onWorkHistoryChange(e.target.value)}
          placeholder={hasResume
            ? "Add anything not covered in your resume..."
            : "Describe your work experience, certifications, or skills..."}
          maxLength={500}
          rows={hasResume ? 2 : 4}
          className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        />
        <p className="text-xs text-muted-foreground text-right">{formData.workHistory.length}/500</p>
      </div>

      <div className="rounded-lg border p-4 bg-muted/30 space-y-2">
        <h3 className="text-sm font-medium">Your Assessment Summary</h3>
        <div className="grid gap-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">ZIP Code</span>
            <span className="font-medium">{formData.zipCode}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Employment</span>
            <span className="font-medium capitalize">{humanizeLabel(formData.employment)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-muted-foreground">Barriers</span>
            <div className="flex gap-1 flex-wrap justify-end">
              {Object.entries(formData.barriers)
                .filter(([, v]) => v)
                .map(([k]) => (
                  <Badge key={k} variant="secondary" className="text-xs capitalize">
                    {humanizeLabel(k)}
                  </Badge>
                ))}
            </div>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Vehicle</span>
            <span className="font-medium">{formData.hasVehicle ? "Yes" : "No"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Schedule</span>
            <span className="font-medium capitalize">{humanizeLabel(formData.availableHours)}</span>
          </div>
          {hasResume && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Resume</span>
              <span className="font-medium">Uploaded</span>
            </div>
          )}
          {hasCreditBarrier && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Credit Score</span>
              <span className="font-medium">{creditData.currentScore}</span>
            </div>
          )}
        </div>
      </div>

      {isPending && (
        <div aria-live="polite" className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Analyzing your profile and matching resources...
        </div>
      )}
      {error && (
        <p role="alert" className="text-sm text-destructive">{error}</p>
      )}
    </div>
  );
}
