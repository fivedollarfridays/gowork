"use client";

import { useEffect, useMemo, useState, useCallback, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { ClipboardList, ListChecks, Clock, CreditCard, FileText, Upload, Briefcase, Home } from "lucide-react";
import { postAssessment, postCredit } from "@/lib/api";
import { WizardShell, type WizardStepConfig } from "@/components/wizard/WizardShell";
import { BarrierForm, type BarrierFormData } from "@/components/wizard/BarrierForm";
import { BenefitsStep, BENEFITS_DEFAULTS } from "@/components/wizard/BenefitsStep";
import type { BenefitsFormData } from "@/lib/types";
import { CreditForm, creditFormCanAdvance, ACCOUNT_AGE_RANGES } from "@/components/wizard/CreditForm";
import { ResumeStep } from "@/components/wizard/ResumeStep";
import { IndustryForm } from "@/components/wizard/IndustryForm";
import { ReviewStep } from "./ReviewStep";
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
import { EMPLOYMENT_OPTIONS, isValidMontgomeryZip } from "@/lib/constants";
import { useDemoMode } from "@/hooks/useDemoMode";

const DEFAULT_FORM_DATA: BarrierFormData = {
  zipCode: "",
  employment: "unemployed",
  barriers: Object.fromEntries(
    Object.values(BarrierType).map(k => [k, false])
  ) as Record<BarrierType, boolean>,
  workHistory: "",
  hasVehicle: false,
  availableHours: AvailableHours.DAYTIME,
};

export default function AssessPage() {
  const router = useRouter();
  const demoData = useDemoMode();

  const [formData, setFormData] = useState<BarrierFormData>(DEFAULT_FORM_DATA);

  useEffect(() => {
    if (demoData) setFormData(demoData);
  }, [demoData]);
  const [resumeText, setResumeText] = useState("");
  const [targetIndustries, setTargetIndustries] = useState<string[]>([]);
  const [certifications, setCertifications] = useState<string[]>([]);
  const [benefitsData, setBenefitsData] = useState<BenefitsFormData>(BENEFITS_DEFAULTS);
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
  const hasResume = resumeText.trim().length > 0;
  const resumeWordCount = useMemo(() => resumeText.split(/\s+/).filter(Boolean).length, [resumeText]);

  const mutation = useMutation({
    mutationFn: postAssessment,
    onSuccess: (data) => {
      if (creditResultRef.current) {
        localStorage.setItem(`credit_${data.session_id}`, JSON.stringify(creditResultRef.current));
      }
      if (data.feedback_token) {
        localStorage.setItem(`feedback_token_${data.session_id}`, data.feedback_token);
      }
      router.push(`/plan?session=${data.session_id}`);
    },
    onError: () => {
      setError("Something went wrong submitting your assessment. Please try again.");
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
          credit_score: creditData.currentScore,
          utilization_percent: creditData.overallUtilization,
          total_accounts: creditData.totalAccounts,
          open_accounts: creditData.openAccounts,
          payment_history_percent: creditData.paymentHistoryPct,
          oldest_account_months: ageRange?.months ?? 24,
          negative_items: creditData.negativeItems,
        });
        setCreditResult(result);
        creditResultRef.current = result;
      } catch {
        setError("Credit check could not be completed. Continuing without credit data.");
      }
    }

    const request: AssessmentRequest = {
      zip_code: formData.zipCode,
      employment_status: formData.employment,
      barriers: formData.barriers,
      work_history: formData.workHistory,
      target_industries: targetIndustries,
      has_vehicle: formData.hasVehicle,
      schedule_constraints: {
        available_days: ["monday", "tuesday", "wednesday", "thursday", "friday"],
        available_hours: formData.availableHours,
      },
      ...(resumeText ? { resume_text: resumeText } : {}),
      ...(certifications.length > 0 ? { certifications } : {}),
      ...(creditResultRef.current ? { credit_result: creditResultRef.current } : {}),
      ...(benefitsData.enrolled_programs.length > 0 || benefitsData.household_size > 1 || benefitsData.current_monthly_income > 0
        ? { benefits_data: benefitsData } : {}),
    };
    mutation.mutate(request);
  }, [formData, creditData, hasCreditBarrier, mutation, resumeText, targetIndustries, certifications, benefitsData]);

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
      title: "Resume",
      icon: <Upload className="h-4 w-4" />,
      canAdvance: () => true,
      content: () => (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold mb-1">Upload Your Resume</h2>
            <p className="text-sm text-muted-foreground">
              Upload a resume to improve your job matches. This step is optional.
            </p>
          </div>
          <ResumeStep resumeText={resumeText} onResumeTextChange={setResumeText} />
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
          {barrierCount === 0 && (
            <p className="text-sm text-muted-foreground">
              Select at least one barrier to continue.
            </p>
          )}
        </div>
      ),
    },
    {
      title: "Benefits",
      icon: <Home className="h-4 w-4" />,
      canAdvance: () => true,
      content: () => (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold mb-1">Household &amp; Benefits</h2>
            <p className="text-sm text-muted-foreground">
              Tell us about your household and any benefits you receive. This helps us show how a new job might affect your benefits. You can skip this step.
            </p>
          </div>
          <BenefitsStep data={benefitsData} onChange={setBenefitsData} />
        </div>
      ),
    },
    {
      title: "Schedule",
      icon: <Clock className="h-4 w-4" />,
      canAdvance: () => true,
      content: () => (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold mb-1">When can you work?</h2>
            <p className="text-sm text-muted-foreground">
              Let us know your availability so we can match you with the right shifts and transit options.
            </p>
          </div>
          <div className="space-y-2">
            <label htmlFor="available-hours" className="text-sm font-medium">Available Hours</label>
            <Select
              value={formData.availableHours}
              onValueChange={(v) => setFormData({ ...formData, availableHours: v as AvailableHours })}
            >
              <SelectTrigger id="available-hours">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={AvailableHours.DAYTIME}>Daytime (8am - 5pm)</SelectItem>
                <SelectItem value={AvailableHours.EVENING}>Evening (5pm - 10pm)</SelectItem>
                <SelectItem value={AvailableHours.NIGHT}>Overnight (10pm - 6am)</SelectItem>
                <SelectItem value={AvailableHours.FLEXIBLE}>Flexible / Any shift</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      ),
    },
    {
      title: "Industries",
      icon: <Briefcase className="h-4 w-4" />,
      canAdvance: () => true,
      content: () => (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold mb-1">Target Industries</h2>
            <p className="text-sm text-muted-foreground">
              Select industries you&apos;re interested in. This helps us find better job matches.
            </p>
          </div>
          <IndustryForm
            targetIndustries={targetIndustries}
            certifications={certifications}
            onIndustriesChange={setTargetIndustries}
            onCertificationsChange={setCertifications}
          />
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
      canAdvance: () => (formData.workHistory.trim().length > 0 || hasResume) && !mutation.isPending,
      content: () => (
        <ReviewStep
          formData={formData}
          hasResume={hasResume}
          resumeWordCount={resumeWordCount}
          creditData={creditData}
          hasCreditBarrier={hasCreditBarrier}
          isPending={mutation.isPending}
          error={error}
          onWorkHistoryChange={(v) => setFormData({ ...formData, workHistory: v })}
        />
      ),
    },
  ], [formData, benefitsData, creditData, zipValid, barrierCount, hasCreditBarrier, mutation.isPending, error, resumeText, resumeWordCount, targetIndustries, certifications, hasResume]);

  return (
    <main className="min-h-screen px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-2xl space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-primary">Workforce Navigator</h1>
          <p className="text-muted-foreground">
            Answer a few questions to get your personalized re-entry plan
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
