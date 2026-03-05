"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { postAssessment } from "@/lib/api";
import type { AssessmentRequest, AssessmentResponse, BarrierType, EmploymentStatus } from "@/lib/types";

const BARRIERS: { key: BarrierType; label: string }[] = [
  { key: "credit", label: "Credit / Financial" },
  { key: "transportation", label: "Transportation" },
  { key: "childcare", label: "Childcare" },
  { key: "housing", label: "Housing" },
  { key: "health", label: "Health" },
  { key: "training", label: "Training / Certification" },
  { key: "criminal_record", label: "Criminal Record" },
];

const EMPLOYMENT_OPTIONS: { value: EmploymentStatus; label: string }[] = [
  { value: "unemployed", label: "Unemployed" },
  { value: "underemployed", label: "Underemployed" },
  { value: "seeking_change", label: "Seeking a career change" },
];

type Step = "zip" | "barriers" | "history" | "results";

export default function AssessPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("zip");
  const [zipCode, setZipCode] = useState("");
  const [employment, setEmployment] = useState<EmploymentStatus>("unemployed");
  const [barriers, setBarriers] = useState<Record<string, boolean>>({});
  const [workHistory, setWorkHistory] = useState("");
  const [hasVehicle, setHasVehicle] = useState(false);
  const [result, setResult] = useState<AssessmentResponse | null>(null);

  const mutation = useMutation({
    mutationFn: postAssessment,
    onSuccess: (data) => {
      setResult(data);
      setStep("results");
    },
  });

  const zipValid = /^361\d{2}$/.test(zipCode);

  function handleSubmit() {
    const request: AssessmentRequest = {
      zip_code: zipCode,
      employment_status: employment,
      barriers: barriers as Record<BarrierType, boolean>,
      work_history: workHistory,
      target_industries: [],
      has_vehicle: hasVehicle,
      schedule_constraints: { available_days: ["monday", "tuesday", "wednesday", "thursday", "friday"], available_hours: "daytime" },
    };
    mutation.mutate(request);
  }

  return (
    <main className="min-h-screen p-8 max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-primary mb-8">Skills Assessment</h1>

      {step === "zip" && (
        <section className="space-y-4">
          <label className="block text-sm font-medium">Montgomery ZIP Code</label>
          <input
            type="text"
            value={zipCode}
            onChange={(e) => setZipCode(e.target.value)}
            placeholder="36104"
            maxLength={5}
            className="w-full rounded-lg border px-4 py-2"
          />
          <label className="block text-sm font-medium mt-4">Employment Status</label>
          <select
            value={employment}
            onChange={(e) => setEmployment(e.target.value as EmploymentStatus)}
            className="w-full rounded-lg border px-4 py-2"
          >
            {EMPLOYMENT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <label className="flex items-center gap-2 mt-4">
            <input type="checkbox" checked={hasVehicle} onChange={(e) => setHasVehicle(e.target.checked)} />
            <span className="text-sm">I have a vehicle</span>
          </label>
          <button
            disabled={!zipValid}
            onClick={() => setStep("barriers")}
            className="rounded-lg bg-primary px-6 py-2 text-primary-foreground font-medium disabled:opacity-50"
          >
            Next
          </button>
          {!zipValid && zipCode.length === 5 && (
            <p className="text-sm text-red-500">Please enter a Montgomery area ZIP (361xx)</p>
          )}
        </section>
      )}

      {step === "barriers" && (
        <section className="space-y-4">
          <p className="text-sm text-muted-foreground">Select any barriers you are currently facing:</p>
          {BARRIERS.map((b) => (
            <label key={b.key} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={barriers[b.key] || false}
                onChange={(e) => setBarriers({ ...barriers, [b.key]: e.target.checked })}
              />
              <span>{b.label}</span>
            </label>
          ))}
          <div className="flex gap-4 mt-4">
            <button onClick={() => setStep("zip")} className="rounded-lg border px-6 py-2">Back</button>
            <button onClick={() => setStep("history")} className="rounded-lg bg-primary px-6 py-2 text-primary-foreground font-medium">
              Next
            </button>
          </div>
        </section>
      )}

      {step === "history" && (
        <section className="space-y-4">
          <label className="block text-sm font-medium">Work History</label>
          <textarea
            value={workHistory}
            onChange={(e) => setWorkHistory(e.target.value)}
            placeholder="Describe your work experience..."
            maxLength={500}
            rows={4}
            className="w-full rounded-lg border px-4 py-2"
          />
          <p className="text-xs text-muted-foreground">{workHistory.length}/500</p>
          <div className="flex gap-4">
            <button onClick={() => setStep("barriers")} className="rounded-lg border px-6 py-2">Back</button>
            <button
              disabled={!workHistory.trim() || mutation.isPending}
              onClick={handleSubmit}
              className="rounded-lg bg-primary px-6 py-2 text-primary-foreground font-medium disabled:opacity-50"
            >
              {mutation.isPending ? "Analyzing..." : "Submit Assessment"}
            </button>
          </div>
          {mutation.isError && (
            <p className="text-sm text-red-500">Error: {mutation.error.message}</p>
          )}
        </section>
      )}

      {step === "results" && result && (
        <section className="space-y-6">
          <div className="rounded-lg border p-4 bg-green-50">
            <h2 className="font-semibold text-lg">Assessment Complete</h2>
            <p className="text-sm text-muted-foreground">Session: {result.session_id}</p>
          </div>

          <div className="rounded-lg border p-4">
            <h3 className="font-medium mb-2">Your Profile</h3>
            <p>Barrier severity: <span className="font-semibold capitalize">{result.profile.barrier_severity}</span></p>
            <p>Barriers: {result.profile.primary_barriers.join(", ") || "None"}</p>
            {result.profile.needs_credit_assessment && (
              <p className="text-amber-600 mt-1">Credit assessment recommended</p>
            )}
            {result.profile.transit_dependent && (
              <p className="text-blue-600 mt-1">Transit-dependent — bus routes included in plan</p>
            )}
          </div>

          {result.plan.immediate_next_steps.length > 0 && (
            <div className="rounded-lg border p-4">
              <h3 className="font-medium mb-2">Immediate Next Steps</h3>
              <ol className="list-decimal list-inside space-y-1">
                {result.plan.immediate_next_steps.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            </div>
          )}

          {result.plan.barriers.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-medium">Barrier Cards</h3>
              {result.plan.barriers.map((card, i) => (
                <div key={i} className="rounded-lg border p-4">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">{card.title}</span>
                    <span className={`text-xs px-2 py-1 rounded ${
                      card.severity === "high" ? "bg-red-100 text-red-700" :
                      card.severity === "medium" ? "bg-yellow-100 text-yellow-700" :
                      "bg-green-100 text-green-700"
                    }`}>
                      {card.severity}
                    </span>
                  </div>
                  {card.timeline_days && <p className="text-sm text-muted-foreground mt-1">~{card.timeline_days} days</p>}
                  <ul className="list-disc list-inside mt-2 text-sm">
                    {card.actions.map((action, j) => <li key={j}>{action}</li>)}
                  </ul>
                </div>
              ))}
            </div>
          )}

          <div className="flex gap-4">
            <button
              onClick={() => router.push(`/plan?session=${result.session_id}`)}
              className="rounded-lg bg-primary px-6 py-2 text-primary-foreground font-medium"
            >
              View Full Plan
            </button>
            {result.profile.needs_credit_assessment && (
              <button
                onClick={() => router.push("/credit")}
                className="rounded-lg bg-secondary px-6 py-2 text-secondary-foreground font-medium"
              >
                Credit Assessment
              </button>
            )}
          </div>
        </section>
      )}
    </main>
  );
}
