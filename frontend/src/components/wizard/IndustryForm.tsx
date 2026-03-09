"use client";

import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import { INDUSTRY_OPTIONS, CERTIFICATION_OPTIONS } from "@/lib/constants";

interface IndustryFormProps {
  targetIndustries: string[];
  certifications: string[];
  onIndustriesChange: (industries: string[]) => void;
  onCertificationsChange: (certs: string[]) => void;
  recommendedIndustries?: string[];
  recommendedCertifications?: string[];
}

export function IndustryForm({
  targetIndustries,
  certifications,
  onIndustriesChange,
  onCertificationsChange,
  recommendedIndustries = [],
  recommendedCertifications = [],
}: IndustryFormProps) {
  function toggleIndustry(value: string) {
    if (targetIndustries.includes(value)) {
      onIndustriesChange(targetIndustries.filter((i) => i !== value));
    } else {
      onIndustriesChange([...targetIndustries, value]);
    }
  }

  function toggleCertification(value: string) {
    if (certifications.includes(value)) {
      onCertificationsChange(certifications.filter((c) => c !== value));
    } else {
      onCertificationsChange([...certifications, value]);
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
        {INDUSTRY_OPTIONS.map((opt) => {
          const checked = targetIndustries.includes(opt.value);
          return (
            <Card
              key={opt.value}
              role="button"
              tabIndex={0}
              onClick={() => toggleIndustry(opt.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  toggleIndustry(opt.value);
                }
              }}
              className={cn(
                "cursor-pointer p-4 transition-colors",
                checked
                  ? "border-secondary bg-secondary/5 ring-1 ring-secondary"
                  : "hover:border-muted-foreground/30"
              )}
            >
              <div className="flex items-center gap-3">
                <Checkbox
                  checked={checked}
                  onCheckedChange={() => toggleIndustry(opt.value)}
                  onClick={(e) => e.stopPropagation()}
                />
                <div className="flex flex-col">
                  <span className="text-sm font-medium">{opt.label}</span>
                  {recommendedIndustries.includes(opt.value) && (
                    <span className="text-[10px] font-semibold text-secondary">Recommended</span>
                  )}
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-medium">
          Do you have any of these certifications?
        </h3>
        <div className="space-y-2">
          {CERTIFICATION_OPTIONS.map((opt) => {
            const checked = certifications.includes(opt.value);
            return (
              <div key={opt.value} className="flex items-center gap-3">
                <Checkbox
                  id={`cert-${opt.value}`}
                  checked={checked}
                  onCheckedChange={() => toggleCertification(opt.value)}
                />
                <label
                  htmlFor={`cert-${opt.value}`}
                  className="text-sm font-medium cursor-pointer"
                >
                  {opt.label}
                  {recommendedCertifications.includes(opt.value) && (
                    <span className="ml-2 text-[10px] font-semibold text-secondary">From Resume</span>
                  )}
                </label>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
