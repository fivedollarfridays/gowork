"use client";

import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Shield, Info } from "lucide-react";
import { RecordType, ChargeCategory } from "@/lib/types";
import type { RecordProfile } from "@/lib/types";

const RECORD_TYPE_OPTIONS = [
  { key: RecordType.FELONY, label: "Felony" },
  { key: RecordType.MISDEMEANOR, label: "Misdemeanor" },
  { key: RecordType.ARREST_ONLY, label: "Arrest only (no conviction)" },
  { key: RecordType.EXPUNGED, label: "Expunged / sealed record" },
] as const;

const CHARGE_CATEGORY_OPTIONS = [
  { key: ChargeCategory.THEFT, label: "Theft / Property" },
  { key: ChargeCategory.DRUG, label: "Drug-related" },
  { key: ChargeCategory.DUI, label: "DUI / Traffic" },
  { key: ChargeCategory.FRAUD, label: "Fraud / Financial" },
  { key: ChargeCategory.VIOLENCE, label: "Violence-related" },
  { key: ChargeCategory.SEX_OFFENSE, label: "Sex offense" },
  { key: ChargeCategory.OTHER, label: "Other" },
] as const;

interface CriminalRecordFormProps {
  data: RecordProfile;
  onChange: (data: RecordProfile) => void;
}

function toggleInList<T>(list: T[], item: T): T[] {
  return list.includes(item)
    ? list.filter((i) => i !== item)
    : [...list, item];
}

export function CriminalRecordForm({ data, onChange }: CriminalRecordFormProps) {
  return (
    <div className="space-y-6">
      <Card className="border-secondary/30 bg-secondary/5 p-4">
        <div className="flex gap-3">
          <Info className="h-5 w-5 text-secondary shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium">Your privacy is protected</p>
            <p className="mt-1 text-muted-foreground">
              This information stays in your session only and is never shared
              with employers. It helps us find fair-chance employers and check
              expungement eligibility.
            </p>
          </div>
        </div>
      </Card>

      <div className="space-y-3">
        <label className="text-sm font-medium flex items-center gap-2">
          <Shield className="h-4 w-4" />
          Record Type
        </label>
        <div className="grid gap-2 grid-cols-1 sm:grid-cols-2">
          {RECORD_TYPE_OPTIONS.map((opt) => (
            <label
              key={opt.key}
              className="flex items-center gap-3 rounded-md border p-3 cursor-pointer hover:bg-muted/50"
            >
              <Checkbox
                checked={data.record_types.includes(opt.key)}
                onCheckedChange={() =>
                  onChange({
                    ...data,
                    record_types: toggleInList(data.record_types, opt.key),
                  })
                }
              />
              <span className="text-sm">{opt.label}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        <label className="text-sm font-medium">Charge Category</label>
        <div className="grid gap-2 grid-cols-1 sm:grid-cols-2">
          {CHARGE_CATEGORY_OPTIONS.map((opt) => (
            <label
              key={opt.key}
              className="flex items-center gap-3 rounded-md border p-3 cursor-pointer hover:bg-muted/50"
            >
              <Checkbox
                checked={data.charge_categories.includes(opt.key)}
                onCheckedChange={() =>
                  onChange({
                    ...data,
                    charge_categories: toggleInList(data.charge_categories, opt.key),
                  })
                }
              />
              <span className="text-sm">{opt.label}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <label htmlFor="years-since" className="text-sm font-medium">
            Years since conviction
          </label>
          <Input
            id="years-since"
            type="number"
            min={0}
            max={50}
            value={data.years_since_conviction ?? ""}
            onChange={(e) =>
              onChange({
                ...data,
                years_since_conviction: e.target.value ? Number(e.target.value) : null,
              })
            }
            placeholder="e.g., 5"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Sentence completed?</label>
          <label className="flex items-center gap-3 rounded-md border p-3 cursor-pointer hover:bg-muted/50">
            <Checkbox
              checked={data.completed_sentence}
              onCheckedChange={(checked) =>
                onChange({ ...data, completed_sentence: checked === true })
              }
            />
            <span className="text-sm">
              Yes, I have completed my sentence (including probation/parole)
            </span>
          </label>
        </div>
      </div>
    </div>
  );
}
