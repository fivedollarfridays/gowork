"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import type { BenefitsFormData } from "@/lib/types";

export const BENEFITS_DEFAULTS: BenefitsFormData = {
  household_size: 1,
  current_monthly_income: 0,
  enrolled_programs: [],
  dependents_under_6: 0,
  dependents_6_to_17: 0,
};

const PROGRAM_OPTIONS = [
  { key: "SNAP", label: "SNAP (Food Stamps)" },
  { key: "TANF", label: "TANF (Cash Assistance)" },
  { key: "Medicaid", label: "Medicaid" },
  { key: "ALL_Kids", label: "ALL Kids (Children's Health)" },
  { key: "Childcare_Subsidy", label: "Childcare Subsidy" },
  { key: "Section_8", label: "Section 8 / Housing Voucher" },
  { key: "LIHEAP", label: "LIHEAP (Energy Assistance)" },
] as const;

interface BenefitsStepProps {
  data: BenefitsFormData;
  onChange: (data: BenefitsFormData) => void;
}

export function BenefitsStep({ data, onChange }: BenefitsStepProps) {
  const hasNone = data.enrolled_programs.length === 0;

  function toggleProgram(key: string, checked: boolean) {
    const updated = checked
      ? [...data.enrolled_programs, key]
      : data.enrolled_programs.filter((p) => p !== key);
    onChange({ ...data, enrolled_programs: updated });
  }

  function toggleNone(checked: boolean) {
    if (checked) {
      onChange({ ...data, enrolled_programs: [] });
    }
  }

  // Show empty string instead of 0 so the placeholder shows and typing doesn't prepend zeros
  const numDisplay = (v: number) => (v === 0 ? "" : String(v));

  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <label htmlFor="household-size" className="text-sm font-medium">
            Household Size
          </label>
          <Input
            id="household-size"
            type="text"
            inputMode="numeric"
            placeholder="1"
            value={data.household_size === 1 ? "" : String(data.household_size)}
            onChange={(e) => {
              const raw = e.target.value.replace(/\D/g, "");
              const num = raw === "" ? 1 : Math.max(1, Math.min(8, parseInt(raw)));
              onChange({ ...data, household_size: num });
            }}
          />
        </div>
        <div className="space-y-2">
          <label htmlFor="monthly-income" className="text-sm font-medium">
            Current Monthly Income
          </label>
          <div className="relative">
            <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">$</span>
            <Input
              id="monthly-income"
              type="text"
              inputMode="numeric"
              placeholder="0"
              className="pl-6"
              value={numDisplay(data.current_monthly_income)}
              onChange={(e) => {
                const raw = e.target.value.replace(/[^\d.]/g, "");
                const num = raw === "" ? 0 : Math.max(0, parseFloat(raw) || 0);
                onChange({ ...data, current_monthly_income: num });
              }}
            />
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <p className="text-sm font-medium">Currently Enrolled Programs</p>
        <div className="grid gap-2 sm:grid-cols-2">
          {PROGRAM_OPTIONS.map((opt) => (
            <div key={opt.key} className="flex items-center gap-2">
              <Checkbox
                id={`prog-${opt.key}`}
                checked={data.enrolled_programs.includes(opt.key)}
                onCheckedChange={(checked) => toggleProgram(opt.key, checked === true)}
              />
              <label htmlFor={`prog-${opt.key}`} className="text-sm cursor-pointer">
                {opt.label}
              </label>
            </div>
          ))}
          <div className="flex items-center gap-2">
            <Checkbox
              id="prog-none"
              checked={hasNone}
              onCheckedChange={(checked) => toggleNone(checked === true)}
            />
            <label htmlFor="prog-none" className="text-sm cursor-pointer">
              None of the above
            </label>
          </div>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <label htmlFor="dep-under-6" className="text-sm font-medium">
            Dependents Under 6
          </label>
          <Input
            id="dep-under-6"
            type="text"
            inputMode="numeric"
            placeholder="0"
            value={numDisplay(data.dependents_under_6)}
            onChange={(e) => {
              const raw = e.target.value.replace(/\D/g, "");
              const num = raw === "" ? 0 : Math.max(0, parseInt(raw));
              onChange({ ...data, dependents_under_6: num });
            }}
          />
        </div>
        <div className="space-y-2">
          <label htmlFor="dep-6-17" className="text-sm font-medium">
            Dependents 6-17
          </label>
          <Input
            id="dep-6-17"
            type="text"
            inputMode="numeric"
            placeholder="0"
            value={numDisplay(data.dependents_6_to_17)}
            onChange={(e) => {
              const raw = e.target.value.replace(/\D/g, "");
              const num = raw === "" ? 0 : Math.max(0, parseInt(raw));
              onChange({ ...data, dependents_6_to_17: num });
            }}
          />
        </div>
      </div>
    </div>
  );
}
