import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { EvidenceChips } from "./EvidenceChips";

export interface ExplainStep {
  step: number;
  title: string;
  why: string;
  barrierTags: string[];
  evidence: string[];
}

interface ExplainStepsProps {
  steps: ExplainStep[];
}

export function ExplainSteps({ steps }: ExplainStepsProps) {
  const [openStep, setOpenStep] = useState<number | null>(null);

  return (
    <ol className="space-y-3">
      {steps.map((s) => (
        <li key={s.step} className="rounded-lg border border-border p-3 text-sm">
          <div className="flex items-start gap-2">
            <span className="font-semibold text-primary">{s.step}.</span>
            <div className="flex-1 space-y-1">
              <p className="font-medium">{s.title}</p>
              <div className="flex flex-wrap gap-1">
                {s.barrierTags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          </div>

          <button
            onClick={() => setOpenStep(openStep === s.step ? null : s.step)}
            className="mt-2 text-xs text-muted-foreground underline"
          >
            Why this step?
          </button>

          {openStep === s.step && (
            <div className="mt-2 space-y-1">
              <p className="text-xs text-muted-foreground">{s.why}</p>
              <EvidenceChips sources={s.evidence} />
            </div>
          )}
        </li>
      ))}
    </ol>
  );
}
