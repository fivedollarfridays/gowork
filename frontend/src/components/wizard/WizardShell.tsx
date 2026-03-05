"use client";

import { useState, type ReactNode } from "react";
import { Check, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

export interface WizardStepConfig {
  title: string;
  icon: ReactNode;
  content: (props: { onNext: () => void; onBack: () => void }) => ReactNode;
  canAdvance?: () => boolean;
}

interface WizardShellProps {
  steps: WizardStepConfig[];
  onComplete: () => void;
  completeLabel?: string;
}

export function WizardShell({ steps, onComplete, completeLabel = "Submit" }: WizardShellProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const totalSteps = steps.length;
  const progressValue = ((currentStep + 1) / totalSteps) * 100;
  const isFirst = currentStep === 0;
  const isLast = currentStep === totalSteps - 1;
  const step = steps[currentStep];
  const canAdvance = step.canAdvance ? step.canAdvance() : true;

  function handleNext() {
    if (!canAdvance) return;
    if (isLast) {
      onComplete();
    } else {
      setCurrentStep((s) => s + 1);
    }
  }

  function handleBack() {
    if (!isFirst) setCurrentStep((s) => s - 1);
  }

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      {/* Step indicator */}
      <nav aria-label="Assessment progress" className="flex items-center justify-between gap-2">
        {steps.map((s, i) => {
          const isCompleted = i < currentStep;
          const isCurrent = i === currentStep;
          return (
            <div key={s.title} className="flex flex-1 flex-col items-center gap-1.5">
              <div
                className={cn(
                  "flex h-9 w-9 items-center justify-center rounded-full border-2 text-sm font-semibold transition-colors",
                  isCompleted && "border-secondary bg-secondary text-secondary-foreground",
                  isCurrent && "border-secondary bg-background text-secondary",
                  !isCompleted && !isCurrent && "border-muted text-muted-foreground"
                )}
              >
                {isCompleted ? <Check className="h-4 w-4" /> : i + 1}
              </div>
              <span
                className={cn(
                  "text-xs text-center hidden sm:block",
                  isCurrent ? "font-medium text-foreground" : "text-muted-foreground"
                )}
              >
                {s.title}
              </span>
            </div>
          );
        })}
      </nav>

      {/* Progress bar */}
      <Progress value={progressValue} className="h-2" />

      {/* Step content */}
      <Card>
        <CardContent className="p-6">
          {step.content({ onNext: handleNext, onBack: handleBack })}
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={handleBack}
          disabled={isFirst}
          className={cn(isFirst && "invisible")}
        >
          <ChevronLeft className="h-4 w-4" />
          Back
        </Button>
        <Button
          onClick={handleNext}
          disabled={!canAdvance}
        >
          {isLast ? completeLabel : "Next"}
          {!isLast && <ChevronRight className="h-4 w-4" />}
        </Button>
      </div>
    </div>
  );
}
