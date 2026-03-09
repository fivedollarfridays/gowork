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

  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <label htmlFor="household-size" className="text-sm font-medium">
            Household Size
          </label>
          <Input
            id="household-size"
            type="number"
            min={1}
            max={8}
            value={data.household_size}
            onChange={(e) =>
              onChange({ ...data, household_size: Math.max(1, Math.min(8, parseInt(e.target.value) || 1)) })
            }
          />
        </div>
        <div className="space-y-2">
          <label htmlFor="monthly-income" className="text-sm font-medium">
            Current Monthly Income ($)
          </label>
          <Input
            id="monthly-income"
            type="number"
            min={0}
            step={50}
            value={data.current_monthly_income}
            onChange={(e) =>
              onChange({ ...data, current_monthly_income: Math.max(0, parseFloat(e.target.value) || 0) })
            }
          />
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
            type="number"
            min={0}
            value={data.dependents_under_6}
            onChange={(e) =>
              onChange({ ...data, dependents_under_6: Math.max(0, parseInt(e.target.value) || 0) })
            }
          />
        </div>
        <div className="space-y-2">
          <label htmlFor="dep-6-17" className="text-sm font-medium">
            Dependents 6-17
          </label>
          <Input
            id="dep-6-17"
            type="number"
            min={0}
            value={data.dependents_6_to_17}
            onChange={(e) =>
              onChange({ ...data, dependents_6_to_17: Math.max(0, parseInt(e.target.value) || 0) })
            }
          />
        </div>
      </div>
    </div>
  );
}
