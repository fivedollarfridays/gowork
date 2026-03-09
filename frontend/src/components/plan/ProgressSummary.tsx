import { CheckCircle } from "lucide-react";

interface ProgressSummaryProps {
  completed: number;
  total: number;
}

export function ProgressSummary({ completed, total }: ProgressSummaryProps) {
  if (total === 0) return null;

  const allDone = completed === total;
  const pct = Math.round((completed / total) * 100);

  return (
    <div className="flex items-center gap-3 rounded-lg border bg-card p-4">
      <CheckCircle
        className={`h-5 w-5 shrink-0 ${allDone ? "text-success" : "text-muted-foreground"}`}
        aria-hidden="true"
      />
      <div className="flex-1 min-w-0 space-y-1">
        <p className="text-sm font-medium">
          {allDone
            ? "All actions complete!"
            : `${completed} of ${total} actions completed`}
        </p>
        <div
          role="progressbar"
          aria-valuenow={completed}
          aria-valuemin={0}
          aria-valuemax={total}
          aria-label={`${completed} of ${total} actions completed`}
          className="h-2 w-full rounded-full bg-muted overflow-hidden"
        >
          <div
            className={`h-full rounded-full transition-all ${allDone ? "bg-success" : "bg-primary"}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </div>
  );
}
