"use client";

import { useDroppable } from "@dnd-kit/core";
import type { ReactNode } from "react";
import { useTranslation } from "@/hooks/useTranslation";
import type { JobApplicationStatus } from "@/lib/api/jobApplications";

interface JobKanbanColumnProps {
  status: JobApplicationStatus;
  count: number;
  children?: ReactNode;
}

const COLUMN_LABEL_KEY: Record<JobApplicationStatus, string> = {
  draft: "jobs.columnDraft",
  applied: "jobs.columnApplied",
  interview: "jobs.columnInterview",
  offer: "jobs.columnOffer",
  rejected: "jobs.columnRejected",
  withdrawn: "jobs.columnWithdrawn",
};

const COLUMN_HEAD_CLS: Record<JobApplicationStatus, string> = {
  draft: "bg-muted text-muted-foreground",
  applied: "bg-primary/10 text-primary",
  interview: "bg-warning/20 text-warning-foreground",
  offer: "bg-success/20 text-success-foreground",
  rejected: "bg-destructive/10 text-destructive",
  withdrawn: "bg-muted text-muted-foreground",
};

/**
 * Droppable kanban column. Keyed by status; dnd-kit treats the column
 * as a drop zone so cards can land on empty columns too.
 */
export function JobKanbanColumn({
  status,
  count,
  children,
}: JobKanbanColumnProps) {
  const { t } = useTranslation();
  const { setNodeRef, isOver } = useDroppable({
    id: `column-${status}`,
    data: { status },
  });

  const label = t(COLUMN_LABEL_KEY[status]);

  return (
    <section
      ref={setNodeRef}
      data-testid={`column-${status}`}
      aria-label={label}
      className={`flex min-w-[220px] flex-1 flex-col rounded-lg border bg-card/50 p-2 ${
        isOver ? "ring-2 ring-primary" : ""
      }`}
    >
      <header className="mb-2 flex items-center justify-between px-1">
        <h2
          className={`inline-flex items-center gap-2 rounded-full px-2 py-0.5 text-xs font-semibold ${COLUMN_HEAD_CLS[status]}`}
        >
          {label}
          <span
            className="rounded-full bg-background/70 px-1.5 text-[10px] font-medium"
            aria-label={`${count}`}
          >
            {count}
          </span>
        </h2>
      </header>

      <div
        className="flex flex-col gap-2 p-1"
        role="list"
        aria-label={`${label} column`}
      >
        {count === 0 ? (
          <p className="px-2 py-4 text-center text-xs italic text-muted-foreground">
            {t("jobs.emptyColumn")}
          </p>
        ) : (
          children
        )}
      </div>
    </section>
  );
}
