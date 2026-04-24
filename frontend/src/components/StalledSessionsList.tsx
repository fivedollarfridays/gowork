"use client";

import { AlertTriangle, Clock, ChevronRight } from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";
import type {
  AdvisorStalledSession,
  AdvisorStallLevel,
} from "@/lib/api/advisor";

export interface StalledSessionsListProps {
  sessions: AdvisorStalledSession[];
  onSelect: (sessionId: string) => void;
}

function severityLabel(
  t: (key: string) => string, level: AdvisorStallLevel,
): string {
  if (level === "hard") return t("advisor.severityHard");
  if (level === "medium") return t("advisor.severityMedium");
  return t("advisor.severitySoft");
}

function severityClass(level: AdvisorStallLevel): string {
  if (level === "hard") {
    return "bg-destructive/15 text-destructive border-destructive/40";
  }
  if (level === "medium") {
    return "bg-secondary text-secondary-foreground border-secondary";
  }
  return "bg-muted text-muted-foreground border-muted";
}

export function StalledSessionsList({
  sessions, onSelect,
}: StalledSessionsListProps) {
  const { t } = useTranslation();

  if (sessions.length === 0) {
    return (
      <p
        role="status"
        className="text-sm text-muted-foreground py-8 text-center"
      >
        {t("advisor.emptyState")}
      </p>
    );
  }

  return (
    <ul className="space-y-2" aria-label={t("advisor.inboxHeading")}>
      {sessions.map((s) => (
        <li key={s.session_id}>
          <button
            type="button"
            data-testid="stalled-session-row"
            onClick={() => onSelect(s.session_id)}
            className="w-full flex items-center gap-3 rounded-lg border bg-card px-4 py-3 text-left hover:bg-accent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            aria-label={`${s.session_id} — ${severityLabel(t, s.stall_level)} — ${s.days_stalled} days`}
          >
            <span
              data-testid={`stall-badge-${s.session_id}`}
              data-stall-level={s.stall_level}
              className={`inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs font-medium ${severityClass(s.stall_level)}`}
            >
              <AlertTriangle className="h-3 w-3" aria-hidden="true" />
              {severityLabel(t, s.stall_level)}
            </span>
            <span className="font-mono text-sm flex-1 truncate">
              {s.session_id}
            </span>
            <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" aria-hidden="true" />
              {t("advisor.daysStalled").replace(
                "{{days}}", String(s.days_stalled),
              )}
            </span>
            <ChevronRight
              className="h-4 w-4 text-muted-foreground"
              aria-hidden="true"
            />
          </button>
        </li>
      ))}
    </ul>
  );
}
