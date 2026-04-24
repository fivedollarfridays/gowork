"use client";

import { useDraggable } from "@dnd-kit/core";
import { Briefcase, Building2, Calendar, FileText } from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";
import type {
  GenerationMethod,
  JobApplication,
} from "@/lib/api/jobApplications";
import { Card, CardContent } from "@/components/ui/card";

interface JobCardProps {
  application: JobApplication;
  resumeGenerationMethod?: GenerationMethod | string | null;
  resumeVersionCounter?: number | null;
  /**
   * Optional fallback status-change handler. When provided, renders a move
   * menu (buttons per target status) for keyboard users without a drag
   * interaction. This keeps the kanban usable without a pointer.
   */
  onChangeStatus?: (application: JobApplication) => void;
}

const GEN_METHOD_KEY: Record<string, string> = {
  llm: "jobs.cardGenMethodLlm",
  template: "jobs.cardGenMethodTemplate",
};

const GEN_METHOD_CLS: Record<string, string> = {
  llm: "bg-primary/10 text-primary",
  template: "bg-muted text-muted-foreground",
};

function formatAppliedDate(applied: string | null): string {
  if (!applied) return "";
  try {
    // Parse as local date. `applied_date` is ISO YYYY-MM-DD.
    const parts = applied.split("-").map((x) => Number(x));
    if (parts.length !== 3) return applied;
    const [y, m, d] = parts;
    const date = new Date(y, m - 1, d);
    return date.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return applied;
  }
}

/**
 * Kanban card for a single job application. Draggable via dnd-kit;
 * keyboard users get an explicit "move" control via `onChangeStatus`.
 */
export function JobCard({
  application,
  resumeGenerationMethod,
  resumeVersionCounter,
  onChangeStatus,
}: JobCardProps) {
  const { t } = useTranslation();
  const a = application;

  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `application-${a.id}`,
    data: { applicationId: a.id, currentStatus: a.status },
  });

  const company = a.company?.trim() || t("jobs.cardCompanyUnknown");
  const role = a.role?.trim() || t("jobs.cardRoleUnknown");
  const appliedOn = formatAppliedDate(a.applied_date);

  const methodKey =
    typeof resumeGenerationMethod === "string"
      ? resumeGenerationMethod
      : null;
  const methodLabel = methodKey
    ? t(GEN_METHOD_KEY[methodKey] || "jobs.cardGenMethodUnknown")
    : null;
  const methodCls = methodKey
    ? GEN_METHOD_CLS[methodKey] || "bg-muted text-muted-foreground"
    : "bg-muted text-muted-foreground";

  return (
    <Card
      ref={setNodeRef}
      data-testid={`job-card-${a.id}`}
      data-application-id={a.id}
      className={`p-0 ${isDragging ? "opacity-60" : ""}`}
      {...attributes}
      {...listeners}
      role="button"
      tabIndex={0}
      aria-label={`${role} — ${company}`}
    >
      <CardContent className="p-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-sm font-semibold text-foreground">
              {role}
            </h3>
            <p className="mt-0.5 inline-flex items-center gap-1 truncate text-xs text-muted-foreground">
              <Building2 className="h-3 w-3" aria-hidden="true" />
              {company}
            </p>
          </div>
          {a.match_source && (
            <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
              <Briefcase className="h-3 w-3" aria-hidden="true" />
              {a.match_source}
            </span>
          )}
        </div>

        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-muted-foreground">
          {appliedOn && (
            <span className="inline-flex items-center gap-1">
              <Calendar className="h-3 w-3" aria-hidden="true" />
              {t("jobs.cardAppliedOn")}: {appliedOn}
            </span>
          )}
          {a.resume_version_id != null && (
            <a
              href={`/api/documents/resume/${a.resume_version_id}/pdf`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-primary hover:underline"
              aria-label={`${t("jobs.cardResumeVersion")}${resumeVersionCounter ?? a.resume_version_id}`}
              onClick={(e) => e.stopPropagation()}
              onPointerDown={(e) => e.stopPropagation()}
              onKeyDown={(e) => e.stopPropagation()}
            >
              <FileText className="h-3 w-3" aria-hidden="true" />
              {t("jobs.cardResumeVersion")}
              {resumeVersionCounter ?? a.resume_version_id}
            </a>
          )}
          {methodLabel && (
            <span
              className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${methodCls}`}
              data-testid={`gen-method-${a.id}`}
            >
              {methodLabel}
            </span>
          )}
        </div>

        {onChangeStatus && (
          <div className="mt-2">
            <button
              type="button"
              className="rounded border border-input bg-background px-2 py-0.5 text-[11px] text-muted-foreground hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
              aria-label={`${t("jobs.cardMoveLabel")}: ${role}`}
              onClick={(e) => {
                e.stopPropagation();
                onChangeStatus(a);
              }}
              onPointerDown={(e) => e.stopPropagation()}
              onKeyDown={(e) => e.stopPropagation()}
            >
              {t("jobs.cardMoveLabel")}
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
