"use client";

import { useMemo, useState, useCallback, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { ClipboardList, ListChecks, CreditCard, FileText, Loader2 } from "lucide-react";
import { postAssessment, postCredit } from "@/lib/api";
import { WizardShell, type WizardStepConfig } from "@/components/wizard/WizardShell";
import { BarrierForm, type BarrierFormData } from "@/components/wizard/BarrierForm";
import { CreditForm, creditFormCanAdvance, ACCOUNT_AGE_RANGES } from "@/components/wizard/CreditForm";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { AvailableHours, BarrierType } from "@/lib/types";
import type { AssessmentRequest, CreditAssessmentResult, CreditFormData, EmploymentStatus } from "@/lib/types";
import { EMPLOYMENT_OPTIONS, isValidMontgomeryZip, humanizeLabel } from "@/lib/constants";

export default function AssessPage() {
  const router = useRouter();

  const [formData, setFormData] = useState<BarrierFormData>({
    zipCode: "",
    employment: "unemployed",
    barriers: Object.fromEntries(
      Object.values(BarrierType).map(k => [k, false])
    ) as Record<BarrierType, boolean>,
    workHistory: "",
    hasVehicle: false,
  });
  const [creditData, setCreditData] = useState<CreditFormData>({
    currentScore: 580,
    overallUtilization: 30,
    paymentHistoryPct: 90,
    accountAgeRange: "",
    totalAccounts: 0,
    openAccounts: 0,
    collectionAccounts: 0,
    negativeItems: [],
  });
  const [creditResult, setCreditResult] = useState<CreditAssessmentResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const zipValid = isValidMontgomeryZip(formData.zipCode);
  const barrierCount = Object.values(formData.barriers).filter(Boolean).length;
  const hasCreditBarrier = formData.barriers[BarrierType.CREDIT];

  const mutation = useMutation({
    mutationFn: postAssessment,
    onSuccess: (data) => {
      if (creditResultRef.current) {
        sessionStorage.setItem(`credit_${data.session_id}`, JSON.stringify(creditResultRef.current));
      }
      router.push(`/plan?session=${data.session_id}`);
    },
    onError: (err) => {
      setError(err.message);
    },
  });

  // Store credit result in a ref so onSuccess can read it synchronously
  const creditResultRef = useRef<CreditAssessmentResult | null>(null);
  creditResultRef.current = creditResult;

  const handleSubmit = useCallback(async () => {
    setError(null);

    // If credit barrier selected, run credit assessment first
    if (hasCreditBarrier && !creditResultRef.current) {
      try {
        const ageRange = ACCOUNT_AGE_RANGES.find((r) => r.value === creditData.accountAgeRange);
        const result = await postCredit({
          current_score: creditData.currentScore,
          score_band: null,
          overall_utilization: creditData.overallUtilization,
          account_summary: {
            total_accounts: creditData.totalAccounts,
            open_accounts: creditData.openAccounts,
            closed_accounts: Math.max(0, creditData.totalAccounts - creditData.openAccounts),
            negative_accounts: creditData.negativeItems.length,
            collection_accounts: creditData.collectionAccounts,
            total_balance: 0,
            total_credit_limit: 0,
            monthly_payments: 0,
          },
          payment_history_pct: creditData.paymentHistoryPct,
          average_account_age_months: ageRange?.months ?? 24,
          negative_items: creditData.negativeItems,
        });
        setCreditResult(result);
        creditResultRef.current = result;
      } catch (err) {
        setError(err instanceof Error ? `Credit check failed: ${err.message}. Continuing without credit data.` : "Credit check failed. Continuing without credit data.");
      }
    }

    const request: AssessmentRequest = {
      zip_code: formData.zipCode,
      employment_status: formData.employment,
      barriers: formData.barriers,
      work_history: formData.workHistory,
      target_industries: [],
      has_vehicle: formData.hasVehicle,
      // Placeholder — no schedule step in wizard yet
      schedule_constraints: {
        available_days: ["monday", "tuesday", "wednesday", "thursday", "friday"],
        available_hours: AvailableHours.DAYTIME,
      },
    };
    mutation.mutate(request);
  }, [formData, creditData, hasCreditBarrier, mutation]);

  const steps: WizardStepConfig[] = useMemo(() => [
    {
      title: "Basic Info",
      icon: <ClipboardList className="h-4 w-4" />,
      canAdvance: () => zipValid,
      content: () => (
        <div className="space-y-6">
          <div>
            <h2 className="text-lg font-semibold mb-1">Tell us about yourself</h2>
            <p className="text-sm text-muted-foreground">
              We serve the Montgomery, Alabama area. Enter your ZIP code to get started.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label htmlFor="zip" className="text-sm font-medium">Montgomery ZIP Code</label>
              <Input
                id="zip"
                type="text"
                value={formData.zipCode}
                onChange={(e) => setFormData({ ...formData, zipCode: e.target.value })}
                placeholder="36104"
                maxLength={5}
              />
              {formData.zipCode.length === 5 && !zipValid && (
                <p className="text-xs text-destructive">Please enter a Montgomery area ZIP (361xx)</p>
              )}
            </div>

            <div className="space-y-2">
              <label htmlFor="employment" className="text-sm font-medium">Employment Status</label>
              <Select
                value={formData.employment}
                onValueChange={(v) => setFormData({ ...formData, employment: v as EmploymentStatus })}
              >
                <SelectTrigger id="employment">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {EMPLOYMENT_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Checkbox
              id="vehicle"
              checked={formData.hasVehicle}
              onCheckedChange={(checked) => setFormData({ ...formData, hasVehicle: checked === true })}
            />
            <label htmlFor="vehicle" className="text-sm font-medium cursor-pointer">
              I have a vehicle
            </label>
          </div>
        </div>
      ),
    },
    {
      title: "Barriers",
      icon: <ListChecks className="h-4 w-4" />,
      canAdvance: () => barrierCount > 0,
      content: () => (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold mb-1">What&apos;s in your way?</h2>
            <p className="text-sm text-muted-foreground">
              Choose all that apply. We&apos;ll match you with resources and jobs that work around these.
            </p>
          </div>
          <BarrierForm data={formData} onChange={setFormData} />
        </div>
      ),
    },
    ...(hasCreditBarrier ? [{
      title: "Credit Check",
      icon: <CreditCard className="h-4 w-4" />,
      canAdvance: () => creditFormCanAdvance(creditData),
      content: () => (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold mb-1">Credit Self-Assessment</h2>
            <p className="text-sm text-muted-foreground">
              Help us understand your credit situation. This stays private and helps us match you with the right resources.
            </p>
          </div>
          <CreditForm data={creditData} onChange={setCreditData} />
        </div>
      ),
    }] as WizardStepConfig[] : []),
    {
      title: "Review & Submit",
      icon: <FileText className="h-4 w-4" />,
      canAdvance: () => formData.workHistory.trim().length > 0 && !mutation.isPending,
      content: () => (
        <div className="space-y-6">
          <div>
            <h2 className="text-lg font-semibold mb-1">Review & Submit</h2>
            <p className="text-sm text-muted-foreground">
              Add your work history and review your information before submitting.
            </p>
          </div>

          <div className="space-y-2">
            <label htmlFor="work-history" className="text-sm font-medium">Work History</label>
            <textarea
              id="work-history"
              value={formData.workHistory}
              onChange={(e) => setFormData({ ...formData, workHistory: e.target.value })}
              placeholder="Describe your work experience, certifications, or skills..."
              maxLength={500}
              rows={4}
              className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            />
            <p className="text-xs text-muted-foreground text-right">{formData.workHistory.length}/500</p>
          </div>

          <div className="rounded-lg border p-4 bg-muted/30 space-y-2">
            <h3 className="text-sm font-medium">Your Assessment Summary</h3>
            <div className="grid gap-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">ZIP Code</span>
                <span className="font-medium">{formData.zipCode}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Employment</span>
                <span className="font-medium capitalize">{humanizeLabel(formData.employment)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Barriers</span>
                <div className="flex gap-1 flex-wrap justify-end">
                  {Object.entries(formData.barriers)
                    .filter(([, v]) => v)
                    .map(([k]) => (
                      <Badge key={k} variant="secondary" className="text-xs capitalize">
                        {humanizeLabel(k)}
                      </Badge>
                    ))}
                </div>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Vehicle</span>
                <span className="font-medium">{formData.hasVehicle ? "Yes" : "No"}</span>
              </div>
              {hasCreditBarrier && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Credit Score</span>
                  <span className="font-medium">{creditData.currentScore}</span>
                </div>
              )}
            </div>
          </div>

          {mutation.isPending && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Analyzing your profile and matching resources...
            </div>
          )}
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
        </div>
      ),
    },
  ], [formData, creditData, zipValid, barrierCount, hasCreditBarrier, mutation.isPending, error]);

  return (
    <main className="min-h-screen px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-2xl space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-primary">Skills Assessment</h1>
          <p className="text-muted-foreground">
            Answer a few questions to get your personalized workforce plan
          </p>
        </div>

        <WizardShell
          steps={steps}
          onComplete={handleSubmit}
          completeLabel={mutation.isPending ? "Analyzing..." : "Submit Assessment"}
        />
      </div>
    </main>
  );
}
