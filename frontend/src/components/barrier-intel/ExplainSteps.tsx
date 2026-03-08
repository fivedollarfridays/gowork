"use client";

import { useState } from "react";
import type { ExplainStep } from "@/lib/types";

interface ExplainStepsProps {
  steps?: ExplainStep[];
}

export function ExplainSteps({ steps }: ExplainStepsProps) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  if (!steps || steps.length === 0) return null;

  function toggle(index: number) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  }

  return (
    <ol className="mt-2 space-y-2" aria-label="Action steps">
      {steps.map((step, i) => (
        <li key={i} className="flex gap-2">
          <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
            {i + 1}
          </span>
          <div className="flex-1">
            <span className="text-sm">{step.text}</span>
            {step.reasoning && (
              <>
                <button
                  type="button"
                  aria-label="Why this step?"
                  className="ml-2 text-xs text-muted-foreground underline hover:text-foreground"
                  onClick={() => toggle(i)}
                >
                  Why this step?
                </button>
                {expanded.has(i) && (
                  <p className="mt-1 text-xs text-muted-foreground italic">
                    {step.reasoning}
                  </p>
                )}
              </>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}
