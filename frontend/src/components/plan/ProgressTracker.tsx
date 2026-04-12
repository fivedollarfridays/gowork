"use client";

import { useEffect } from "react";
import { CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import { getTranslation, getLocale } from "@/lib/i18n";

export interface ProgressStep {
  key: string;
  label: string;
  completed: boolean;
}

interface ProgressTrackerProps {
  steps: ProgressStep[];
  onToggle: (key: string, completed: boolean) => void;
  planId?: string;
}

const STORAGE_PREFIX = "plan-progress-";

function getStorageKey(planId?: string): string {
  return `${STORAGE_PREFIX}${planId ?? "default"}`;
}

function loadProgress(planId?: string): Set<string> {
  if (typeof window === "undefined") return new Set();
  try {
    const raw = localStorage.getItem(getStorageKey(planId));
    if (raw) return new Set(JSON.parse(raw));
  } catch {
    /* ignore parse errors */
  }
  return new Set();
}

function saveProgress(completedKeys: string[], planId?: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(getStorageKey(planId), JSON.stringify(completedKeys));
  } catch {
    /* ignore storage errors */
  }
}

function CompletionSummary({ done, total }: { done: number; total: number }) {
  const locale = getLocale();
  const completedLabel = getTranslation("progressTracker.completed", locale);
  const remainingLabel = getTranslation("progressTracker.remaining", locale);
  return (
    <div className="flex gap-4 text-sm">
      <span className="text-success font-medium">{done} {completedLabel}</span>
      <span className="text-muted-foreground">{total - done} {remainingLabel}</span>
    </div>
  );
}

export function ProgressTracker({ steps, onToggle, planId }: ProgressTrackerProps) {
  const locale = getLocale();
  const heading = getTranslation("progressTracker.heading", locale);
  const description = getTranslation("progressTracker.description", locale);
  const allDoneMsg = getTranslation("progressTracker.allDone", locale);

  // Restore saved progress on mount
  useEffect(() => {
    const saved = loadProgress(planId);
    for (const key of saved) {
      const step = steps.find((s) => s.key === key);
      if (step && !step.completed) {
        onToggle(key, true);
      }
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Save progress when steps change
  useEffect(() => {
    const completedKeys = steps.filter((s) => s.completed).map((s) => s.key);
    if (completedKeys.length > 0) {
      saveProgress(completedKeys, planId);
    }
  }, [steps, planId]);

  const completedCount = steps.filter((s) => s.completed).length;
  const pct = steps.length > 0 ? Math.round((completedCount / steps.length) * 100) : 0;
  const allDone = steps.length > 0 && completedCount === steps.length;

  return (
    <section className="space-y-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium">{heading}</CardTitle>
          <p className="text-sm text-muted-foreground">{description}</p>
        </CardHeader>
        <CardContent className="space-y-4">
          <Progress value={pct} aria-label={`${pct}% complete`} />
          <CompletionSummary done={completedCount} total={steps.length} />

          {allDone && (
            <div className="flex items-center gap-2 rounded-md bg-success/10 px-3 py-2 text-sm text-success">
              <CheckCircle2 className="h-4 w-4" />
              {allDoneMsg}
            </div>
          )}

          <ul className="space-y-2" role="list" aria-label={heading}>
            {steps.map((step) => (
              <li key={step.key} className="flex items-center gap-3">
                <Checkbox
                  id={step.key}
                  checked={step.completed}
                  onCheckedChange={(checked) =>
                    onToggle(step.key, checked === true)
                  }
                  aria-label={step.label}
                />
                <label
                  htmlFor={step.key}
                  className={`text-sm cursor-pointer ${
                    step.completed
                      ? "line-through text-muted-foreground"
                      : "text-foreground"
                  }`}
                >
                  {step.label}
                </label>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </section>
  );
}
