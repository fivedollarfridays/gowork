"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { postCredit } from "@/lib/api";
import type { CreditAssessmentResult, CreditProfileRequest } from "@/lib/types";
import { SEVERITY_BADGE_STYLES } from "@/lib/constants";

export default function CreditPage() {
  const [score, setScore] = useState("");
  const [utilization, setUtilization] = useState("");
  const [paymentHistory, setPaymentHistory] = useState("");
  const [accountAge, setAccountAge] = useState("");
  const [totalAccounts, setTotalAccounts] = useState("");
  const [openAccounts, setOpenAccounts] = useState("");
  const [result, setResult] = useState<CreditAssessmentResult | null>(null);

  const mutation = useMutation({
    mutationFn: postCredit,
    onSuccess: (data) => setResult(data),
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const request: CreditProfileRequest = {
      credit_score: parseInt(score, 10),
      utilization_percent: parseFloat(utilization),
      total_accounts: parseInt(totalAccounts, 10) || 1,
      open_accounts: parseInt(openAccounts, 10) || 1,
      payment_history_percent: parseFloat(paymentHistory),
      oldest_account_months: parseInt(accountAge, 10),
      negative_items: [],
    };
    mutation.mutate(request);
  }

  const formValid = score && utilization && paymentHistory && accountAge;

  return (
    <main className="min-h-screen p-8 max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-primary mb-8">Credit Assessment</h1>

      {!result ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium">Credit Score (300-850)</label>
            <input
              type="number" min={300} max={850} value={score}
              onChange={(e) => setScore(e.target.value)}
              className="w-full rounded-lg border px-4 py-2" required
            />
          </div>
          <div>
            <label className="block text-sm font-medium">Credit Utilization (%)</label>
            <input
              type="number" min={0} max={100} step={0.1} value={utilization}
              onChange={(e) => setUtilization(e.target.value)}
              className="w-full rounded-lg border px-4 py-2" required
            />
          </div>
          <div>
            <label className="block text-sm font-medium">Payment History (%)</label>
            <input
              type="number" min={0} max={100} step={0.1} value={paymentHistory}
              onChange={(e) => setPaymentHistory(e.target.value)}
              className="w-full rounded-lg border px-4 py-2" required
            />
          </div>
          <div>
            <label className="block text-sm font-medium">Average Account Age (months)</label>
            <input
              type="number" min={0} value={accountAge}
              onChange={(e) => setAccountAge(e.target.value)}
              className="w-full rounded-lg border px-4 py-2" required
            />
          </div>
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium">Total Accounts</label>
              <input
                type="number" min={0} value={totalAccounts}
                onChange={(e) => setTotalAccounts(e.target.value)}
                className="w-full rounded-lg border px-4 py-2"
              />
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium">Open Accounts</label>
              <input
                type="number" min={0} value={openAccounts}
                onChange={(e) => setOpenAccounts(e.target.value)}
                className="w-full rounded-lg border px-4 py-2"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={!formValid || mutation.isPending}
            className="rounded-lg bg-primary px-6 py-2 text-primary-foreground font-medium disabled:opacity-50"
          >
            {mutation.isPending ? "Analyzing..." : "Assess Credit"}
          </button>
          {mutation.isError && (
            <div role="alert" className="flex items-center gap-3">
              <p className="text-sm text-destructive">Error: {mutation.error.message}</p>
              <button
                type="button"
                onClick={() => mutation.reset()}
                className="text-sm text-primary underline hover:no-underline"
              >
                Try Again
              </button>
            </div>
          )}
        </form>
      ) : (
        <div className="space-y-6">
          <div className={`rounded-lg border p-4 ${
            SEVERITY_BADGE_STYLES[result.barrier_severity as keyof typeof SEVERITY_BADGE_STYLES] ?? SEVERITY_BADGE_STYLES.low
          }`}>
            <h2 className="font-semibold text-lg">
              Barrier Severity: <span className="capitalize">{result.barrier_severity}</span>
            </h2>
          </div>

          {result.thresholds.length > 0 && (
            <div className="rounded-lg border p-4">
              <h3 className="font-medium mb-2">Credit Thresholds</h3>
              {result.thresholds.map((t, i) => (
                <div key={i} className="flex justify-between py-1 border-b last:border-0">
                  <span>{String(t.threshold_name || "")}</span>
                  <span className="text-sm text-muted-foreground">
                    {t.already_met ? "Met" : `~${t.estimated_days} days`}
                  </span>
                </div>
              ))}
            </div>
          )}

          {result.eligibility.length > 0 && (
            <div className="rounded-lg border p-4">
              <h3 className="font-medium mb-2">Product Eligibility</h3>
              {result.eligibility.map((e, i) => (
                <div key={i} className="flex justify-between py-1 border-b last:border-0">
                  <span>{String(e.product_name || "")}</span>
                  <span className={`text-sm ${e.status === "eligible" ? "text-success" : "text-accent-foreground"}`}>
                    {String(e.status || "")}
                  </span>
                </div>
              ))}
            </div>
          )}

          <p className="text-xs text-muted-foreground">{result.disclaimer}</p>

          <button
            onClick={() => setResult(null)}
            className="rounded-lg border px-6 py-2"
          >
            Run Another Assessment
          </button>
        </div>
      )}
    </main>
  );
}
