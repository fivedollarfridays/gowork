"use client";

import { useEffect, useMemo, useState, useCallback, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { ClipboardList, ListChecks, Clock, CreditCard, FileText, Upload, Briefcase, Home, Shield } from "lucide-react";
import { postAssessment, postCredit } from "@/lib/api";
import { WizardShell, type WizardStepConfig } from "@/components/wizard/WizardShell";
import { BarrierForm, type BarrierFormData } from "@/components/wizard/BarrierForm";
import { BenefitsStep, BENEFITS_DEFAULTS } from "@/components/wizard/BenefitsStep";
import { CreditForm, creditFormCanAdvance, ACCOUNT_AGE_RANGES } from "@/components/wizard/CreditForm";
import { CriminalRecordForm } from "@/components/wizard/CriminalRecordForm";
import { ResumeStep } from "@/components/wizard/ResumeStep";
import { IndustryForm } from "@/components/wizard/IndustryForm";
import { ReviewStep } from "./ReviewStep";
import { Input } from "@/components/ui/input";
import type { BenefitsFormData } from "@/lib/types";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { AvailableHours, BarrierType } from "@/lib/types";
import type { AssessmentRequest, CreditAssessmentResult, CreditFormData, EmploymentStatus, RecordProfile } from "@/lib/types";
import { EMPLOYMENT_OPTIONS, isValidCityZip, humanizeLabel, getCityAreaDescription, getZipPlaceholder, getZipErrorMessage } from "@/lib/constants";
import { useDemoMode } from "@/hooks/useDemoMode";
import { useCityConfig } from "@/hooks/useCityConfig";
import { getResumeRecommendations } from "@/lib/resume/recommend";
import { t } from "@/lib/i18n";
import { WALL_TO_ASSESS_TRANSITION_NAME } from "@/lib/wall/viewTransitions";

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
  const city = useCityConfig();
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
  const [recordProfile, setRecordProfile] = useState<RecordProfile>({
    record_types: [],
    charge_categories: [],
    years_since_conviction: null,
    completed_sentence: false,
  });
  const [error, setError] = useState<string | null>(null);

  const zipValid = isValidCityZip(formData.zipCode, city.state);
  const barrierCount = Object.values(formData.barriers).filter(Boolean).length;
  const hasCreditBarrier = formData.barriers[BarrierType.CREDIT];
  const hasCriminalBarrier = formData.barriers[BarrierType.CRIMINAL_RECORD];
  const hasResume = resumeText.trim().length > 0;
  const resumeWordCount = useMemo(() => resumeText.split(/\s+/).filter(Boolean).length, [resumeText]);
  const resumeRecs = useMemo(() => getResumeRecommendations(resumeText), [resumeText]);

  useEffect(() => {
    if (resumeRecs.certifications.length > 0) {
      setCertifications((prev) => {
        const merged = new Set([...prev, ...resumeRecs.certifications]);
        return merged.size !== prev.length ? Array.from(merged) : prev;
      });
    }
  }, [resumeRecs.certifications]);

  const mutation = useMutation({
    mutationFn: postAssessment,
    onSuccess: (data) => {
      if (creditResultRef.current) {
        sessionStorage.setItem(`credit_${data.session_id}`, JSON.stringify(creditResultRef.current));
      }
      if (data.feedback_token) {
        sessionStorage.setItem(`feedback_token_${data.session_id}`, data.feedback_token);
      }
      sessionStorage.setItem(`zip_${data.session_id}`, formData.zipCode);
      if (benefitsData.enrolled_programs.length > 0) {
        sessionStorage.setItem(`enrolled_${data.session_id}`, JSON.stringify(benefitsData.enrolled_programs));
      }
      router.push(`/plan?session=${data.session_id}`);
    },
    onError: () => {
      setError(t("assess.errorSubmit"));
    },
  });

  // Store credit result in a ref so onSuccess can read it synchronously
  const creditResultRef = useRef<CreditAssessmentResult | null>(null);
  creditResultRef.current = creditResult;

  const handleSubmit = useCallback(async () => {
    setError(null);
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
        setError(t("assess.errorCredit"));
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
      ...(hasCriminalBarrier && recordProfile.record_types.length > 0 ? { record_profile: recordProfile } : {}),
      ...(benefitsData.enrolled_programs.length > 0 || benefitsData.household_size > 1 || benefitsData.current_monthly_income > 0
        ? { benefits_data: benefitsData } : {}),
    };
    mutation.mutate(request);
  }, [formData, creditData, hasCreditBarrier, hasCriminalBarrier, mutation, resumeText, targetIndustries, certifications, recordProfile, benefitsData]);

  const steps: WizardStepConfig[] = useMemo(() => [
    {
      title: t("assess.stepBasicInfo"),
      icon: <ClipboardList className="h-4 w-4" />,
      canAdvance: () => zipValid,
      content: () => (
        <div className="space-y-6">
          <div>
            <h2 className="text-lg font-semibold mb-1">{t("assess.basicInfoTitle")}</h2>
            <p className="text-sm text-muted-foreground">
              {getCityAreaDescription(city.state)}
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label htmlFor="zip" className="text-sm font-medium">{t("assess.zipLabel")}</label>
              <Input
                id="zip"
                type="text"
                value={formData.zipCode}
                onChange={(e) => setFormData({ ...formData, zipCode: e.target.value })}
                placeholder={getZipPlaceholder(city.state)}
                maxLength={5}
              />
              {formData.zipCode.length === 5 && !zipValid && (
                <p className="text-xs text-destructive">{getZipErrorMessage(city.state)}</p>
              )}
            </div>

            <div className="space-y-2">
              <label htmlFor="employment" className="text-sm font-medium">{t("assess.employmentLabel")}</label>
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
              {t("assess.iHaveVehicle")}
            </label>
          </div>
        </div>
      ),
    },
    {
      title: t("assess.stepResume"),
      icon: <Upload className="h-4 w-4" />,
      canAdvance: () => true,
      content: () => (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold mb-1">{t("assess.resumeTitle")}</h2>
            <p className="text-sm text-muted-foreground">
              {t("assess.resumeDesc")}
            </p>
          </div>
          <ResumeStep resumeText={resumeText} onResumeTextChange={setResumeText} />
        </div>
      ),
    },
    {
      title: t("assess.stepBarriers"),
      icon: <ListChecks className="h-4 w-4" />,
      canAdvance: () => barrierCount > 0,
      content: () => (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold mb-1">{t("assess.barriersTitle")}</h2>
            <p className="text-sm text-muted-foreground">
              {t("assess.barriersDesc")}
            </p>
          </div>
          <BarrierForm data={formData} onChange={setFormData} />
          {barrierCount === 0 && (
            <p className="text-sm text-muted-foreground">
              {t("assess.barriersMinOne")}
            </p>
          )}
        </div>
      ),
    },
    ...(hasCriminalBarrier ? [{
      title: t("assess.stepRecord"),
      icon: <Shield className="h-4 w-4" />,
      canAdvance: () => true,
      content: () => (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold mb-1">{t("assess.recordTitle")}</h2>
            <p className="text-sm text-muted-foreground">
              {t("assess.recordDesc")}
            </p>
          </div>
          <CriminalRecordForm data={recordProfile} onChange={setRecordProfile} />
        </div>
      ),
    }] as WizardStepConfig[] : []),
    {
      title: t("assess.stepBenefits"),
      icon: <Home className="h-4 w-4" />,
      canAdvance: () => true,
      content: () => (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold mb-1">{t("assess.benefitsTitle")}</h2>
            <p className="text-sm text-muted-foreground">
              {t("assess.benefitsDesc")}
            </p>
          </div>
          <BenefitsStep data={benefitsData} onChange={setBenefitsData} />
        </div>
      ),
    },
    {
      title: t("assess.stepSchedule"),
      icon: <Clock className="h-4 w-4" />,
      canAdvance: () => true,
      content: () => (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold mb-1">{t("assess.scheduleTitle")}</h2>
            <p className="text-sm text-muted-foreground">
              {t("assess.scheduleDesc")}
            </p>
          </div>
          <div className="space-y-2">
            <label htmlFor="available-hours" className="text-sm font-medium">{t("assess.scheduleLabel")}</label>
            <Select
              value={formData.availableHours}
              onValueChange={(v) => setFormData({ ...formData, availableHours: v as AvailableHours })}
            >
              <SelectTrigger id="available-hours">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={AvailableHours.DAYTIME}>{t("assess.daytime")}</SelectItem>
                <SelectItem value={AvailableHours.EVENING}>{t("assess.evening")}</SelectItem>
                <SelectItem value={AvailableHours.NIGHT}>{t("assess.overnight")}</SelectItem>
                <SelectItem value={AvailableHours.FLEXIBLE}>{t("assess.flexible")}</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      ),
    },
    {
      title: t("assess.stepIndustries"),
      icon: <Briefcase className="h-4 w-4" />,
      canAdvance: () => true,
      content: () => (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold mb-1">{t("assess.industriesTitle")}</h2>
            <p className="text-sm text-muted-foreground">
              {t("assess.industriesDesc")}
            </p>
          </div>
          <IndustryForm
            targetIndustries={targetIndustries}
            certifications={certifications}
            onIndustriesChange={setTargetIndustries}
            onCertificationsChange={setCertifications}
            recommendedIndustries={resumeRecs.industries}
            recommendedCertifications={resumeRecs.certifications}
          />
        </div>
      ),
    },
    ...(hasCreditBarrier ? [{
      title: t("assess.stepCredit"),
      icon: <CreditCard className="h-4 w-4" />,
      canAdvance: () => creditFormCanAdvance(creditData),
      content: () => (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold mb-1">{t("assess.creditTitle")}</h2>
            <p className="text-sm text-muted-foreground">
              {t("assess.creditDesc")}
            </p>
          </div>
          <CreditForm data={creditData} onChange={setCreditData} />
        </div>
      ),
    }] as WizardStepConfig[] : []),
    {
      title: t("assess.stepReview"),
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
  ], [formData, benefitsData, creditData, zipValid, barrierCount, hasCreditBarrier, hasCriminalBarrier, recordProfile, mutation.isPending, error, resumeText, resumeWordCount, targetIndustries, certifications, hasResume, resumeRecs, city.state]);

  return (
    <main className="min-h-screen px-4 py-8 sm:px-8">
      {/* W3 Driver C T3.21 — view-transition-name pairs with Chapter 10's
          morph-target so Chrome users see the cinematic Mapbox→form
          morph. Firefox users get a standard navigation (no morph).
          The name lives in `WALL_TO_ASSESS_TRANSITION_NAME` so any
          future refactor changes one constant in one place. */}
      <div
        className="mx-auto max-w-2xl space-y-6"
        data-testid="assess-hero-morph-target"
        style={{ viewTransitionName: WALL_TO_ASSESS_TRANSITION_NAME }}
      >
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-primary">{t("assess.navTitle")}</h1>
          <p className="text-muted-foreground">
            {t("assess.navDesc")}
          </p>
          <p className="text-xs text-muted-foreground/70 flex items-center justify-center gap-1">
            <Shield className="h-3 w-3" />
            {t("assess.privacyBadge")}
          </p>
        </div>

        <WizardShell
          steps={steps}
          onComplete={handleSubmit}
          completeLabel={mutation.isPending ? t("assess.analyzing") : t("assess.submitAssessment")}
        />
      </div>
    </main>
  );
}
