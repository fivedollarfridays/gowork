"use client";

import { useState, useCallback } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { validateFeedbackToken, submitVisitFeedback } from "@/lib/api";

const Q1_OPTIONS = [
  { value: 2, label: "Yes" },
  { value: 1, label: "Not yet" },
  { value: 0, label: "Went elsewhere" },
] as const;

const Q2_OUTCOMES = [
  { value: "wioa_enrolled", label: "WIOA enrollment" },
  { value: "training_referral", label: "Training referral" },
  { value: "childcare_help", label: "Childcare assistance" },
  { value: "resume_help", label: "Resume help" },
  { value: "got_interview", label: "Got an interview" },
  { value: "other", label: "Other" },
] as const;

const Q3_OPTIONS = [
  { value: 3, label: "Yes, it was helpful" },
  { value: 2, label: "Mostly" },
  { value: 1, label: "Not really" },
] as const;

interface RadioGroupProps {
  name: string;
  options: ReadonlyArray<{ value: number; label: string }>;
  selected: number | null;
  onChange: (value: number) => void;
}

function RadioGroup({ name, options, selected, onChange }: RadioGroupProps) {
  return (
    <div className="flex flex-col gap-2">
      {options.map((opt) => (
        <label
          key={opt.value}
          className={cn(
            "flex min-h-11 cursor-pointer items-center gap-3 rounded-lg border px-4 py-3 text-sm transition-colors",
            selected === opt.value
              ? "border-primary bg-primary/5"
              : "border-input hover:border-primary/50",
          )}
        >
          <input
            type="radio"
            name={name}
            value={opt.value}
            checked={selected === opt.value}
            onChange={() => onChange(opt.value)}
            className="accent-primary"
            aria-label={opt.label}
          />
          {opt.label}
        </label>
      ))}
    </div>
  );
}

interface CheckboxGroupProps {
  options: ReadonlyArray<{ value: string; label: string }>;
  selected: string[];
  onChange: (values: string[]) => void;
}

function CheckboxGroup({ options, selected, onChange }: CheckboxGroupProps) {
  return (
    <div className="flex flex-col gap-2">
      {options.map((opt) => {
        const isSelected = selected.includes(opt.value);
        return (
          <label
            key={opt.value}
            className={cn(
              "flex min-h-11 cursor-pointer items-center gap-3 rounded-lg border px-4 py-3 text-sm transition-colors",
              isSelected
                ? "border-primary bg-primary/5"
                : "border-input hover:border-primary/50",
            )}
          >
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => {
                onChange(
                  isSelected
                    ? selected.filter((v) => v !== opt.value)
                    : [...selected, opt.value],
                );
              }}
              className="accent-primary"
            />
            {opt.label}
          </label>
        );
      })}
    </div>
  );
}

export default function FeedbackPage({ params }: { params: { token: string } }) {
  const { token } = params;

  const { data, isLoading, error } = useQuery({
    queryKey: ["validateToken", token],
    queryFn: () => validateFeedbackToken(token),
  });

  const [q1, setQ1] = useState<number | null>(null);
  const [outcomes, setOutcomes] = useState<string[]>([]);
  const [q3, setQ3] = useState<number | null>(null);
  const [freeText, setFreeText] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [duplicateError, setDuplicateError] = useState(false);

  const mutation = useMutation({
    mutationFn: submitVisitFeedback,
    onSuccess: () => setSubmitted(true),
    onError: (err) => {
      const msg = err instanceof Error ? err.message : "";
      if (msg.toLowerCase().includes("already submitted")) {
        setDuplicateError(true);
      }
    },
  });

  const canSubmit = q1 !== null && q3 !== null && !mutation.isPending;

  const handleSubmit = useCallback(() => {
    if (q1 === null || q3 === null) return;
    mutation.mutate({
      token,
      made_it_to_center: q1,
      outcomes: q1 === 2 ? outcomes : [],
      plan_accuracy: q3,
      free_text: freeText,
    });
  }, [token, q1, outcomes, q3, freeText, mutation]);

  // Loading state
  if (isLoading) {
    return (
      <main className="min-h-screen flex items-center justify-center px-4">
        <div aria-label="Loading" className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          Validating your feedback link...
        </div>
      </main>
    );
  }

  // Error / expired / invalid
  if (error || !data?.valid) {
    return (
      <main className="min-h-screen flex items-center justify-center px-4">
        <Card className="w-full max-w-md text-center">
          <CardContent className="pt-6 space-y-4">
            <p className="text-muted-foreground">
              This feedback link is expired or invalid.
            </p>
            <Button asChild variant="outline">
              <a href="/assess">Start a new assessment</a>
            </Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  // Already submitted (duplicate)
  if (duplicateError) {
    return (
      <main className="min-h-screen flex items-center justify-center px-4">
        <Card className="w-full max-w-md text-center">
          <CardContent className="pt-6 space-y-3">
            <p className="font-medium">Already submitted</p>
            <p className="text-sm text-muted-foreground">
              You&apos;ve already shared your feedback for this visit. Thank you!
            </p>
          </CardContent>
        </Card>
      </main>
    );
  }

  // Success / thank you
  if (submitted) {
    return (
      <main className="min-h-screen flex items-center justify-center px-4">
        <Card className="w-full max-w-md text-center">
          <CardContent className="pt-6 space-y-3">
            <p className="text-lg font-semibold">Thank you!</p>
            <p className="text-sm text-muted-foreground">
              Your feedback helps us improve MontGoWork for everyone in Montgomery.
            </p>
          </CardContent>
        </Card>
      </main>
    );
  }

  // Form
  return (
    <main className="min-h-screen px-4 py-8">
      <div className="mx-auto max-w-md space-y-6">
        <div className="text-center space-y-1">
          <h1 className="text-2xl font-bold text-primary">How did it go?</h1>
          <p className="text-sm text-muted-foreground">
            3 quick questions — takes under a minute
          </p>
        </div>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">
              Did you make it to the Montgomery Career Center?
            </CardTitle>
          </CardHeader>
          <CardContent>
            <RadioGroup name="q1" options={Q1_OPTIONS} selected={q1} onChange={setQ1} />
          </CardContent>
        </Card>

        {q1 === 2 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">
                What happened during your visit?
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CheckboxGroup
                options={Q2_OUTCOMES}
                selected={outcomes}
                onChange={setOutcomes}
              />
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">
              Did MontGoWork&apos;s plan prepare you well?
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <RadioGroup name="q3" options={Q3_OPTIONS} selected={q3} onChange={setQ3} />
            <textarea
              value={freeText}
              onChange={(e) => setFreeText(e.target.value)}
              placeholder="Anything else you'd like to share? (optional)"
              maxLength={500}
              rows={3}
              className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            />
          </CardContent>
        </Card>

        <Button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="w-full min-h-11"
        >
          {mutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Submitting...
            </>
          ) : (
            "Submit Feedback"
          )}
        </Button>
      </div>
    </main>
  );
}
