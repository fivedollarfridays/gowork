"use client";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { humanizeLabel } from "@/lib/constants";
import type { CreditFormData } from "@/lib/types";

const SCORE_BANDS: { label: string; min: number; max: number; color: string }[] = [
  { label: "Very Poor", min: 300, max: 599, color: "text-destructive" },
  { label: "Poor", min: 600, max: 649, color: "text-destructive" },
  { label: "Fair", min: 650, max: 699, color: "text-accent-foreground" },
  { label: "Good", min: 700, max: 749, color: "text-success" },
  { label: "Excellent", min: 750, max: 850, color: "text-success" },
];

function getScoreBand(score: number) {
  return SCORE_BANDS.find((b) => score >= b.min && score <= b.max) ?? SCORE_BANDS[0];
}

function utilizationColor(pct: number): string {
  if (pct <= 30) return "text-success";
  if (pct <= 50) return "text-accent-foreground";
  return "text-destructive";
}

const ACCOUNT_AGE_RANGES: { value: string; label: string; months: number }[] = [
  { value: "0-6", label: "Less than 6 months", months: 3 },
  { value: "6-12", label: "6-12 months", months: 9 },
  { value: "1-3y", label: "1-3 years", months: 24 },
  { value: "3-7y", label: "3-7 years", months: 60 },
  { value: "7+", label: "7+ years", months: 108 },
];

const NEGATIVE_ITEM_OPTIONS = [
  "late_payments",
  "collections",
  "bankruptcy",
  "charge_offs",
  "liens",
  "judgments",
];


interface CreditFormProps {
  data: CreditFormData;
  onChange: (data: CreditFormData) => void;
}

export function creditFormCanAdvance(data: CreditFormData): boolean {
  return (
    data.currentScore >= 300 &&
    data.currentScore <= 850 &&
    data.accountAgeRange !== "" &&
    data.totalAccounts > 0
  );
}

export function CreditForm({ data, onChange }: CreditFormProps) {
  const band = getScoreBand(data.currentScore);

  function update(patch: Partial<CreditFormData>) {
    onChange({ ...data, ...patch });
  }

  function toggleNegativeItem(item: string) {
    const items = data.negativeItems.includes(item)
      ? data.negativeItems.filter((i) => i !== item)
      : [...data.negativeItems, item];
    update({ negativeItems: items });
  }

  return (
    <div className="space-y-6">
      {/* Credit Health indicator */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-muted-foreground">Credit Health:</span>
        <Badge
          variant="outline"
          className={cn("capitalize", band.color)}
        >
          {band.label} ({data.currentScore})
        </Badge>
      </div>

      {/* Credit Score */}
      <Card className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium">Credit Score</label>
          <span className={cn("text-sm font-semibold", band.color)}>
            {data.currentScore}
          </span>
        </div>
        <Slider
          min={300}
          max={850}
          step={5}
          value={[data.currentScore]}
          onValueChange={([v]) => update({ currentScore: v })}
          className="w-full"
        />
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>300</span>
          <span>850</span>
        </div>
      </Card>

      {/* Utilization */}
      <Card className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium">Credit Utilization</label>
          <span className={cn("text-sm font-semibold", utilizationColor(data.overallUtilization))}>
            {data.overallUtilization}%
          </span>
        </div>
        <Slider
          min={0}
          max={100}
          step={1}
          value={[data.overallUtilization]}
          onValueChange={([v]) => update({ overallUtilization: v })}
          className="w-full"
        />
        <p className="text-xs text-muted-foreground">
          Percentage of available credit you&apos;re currently using. Below 30% is ideal.
        </p>
      </Card>

      {/* Payment History */}
      <Card className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium">On-time Payment History</label>
          <span className="text-sm font-semibold">{data.paymentHistoryPct}%</span>
        </div>
        <Slider
          min={0}
          max={100}
          step={1}
          value={[data.paymentHistoryPct]}
          onValueChange={([v]) => update({ paymentHistoryPct: v })}
          className="w-full"
        />
        <p className="text-xs text-muted-foreground">
          What percentage of your payments have been on time?
        </p>
      </Card>

      {/* Account Age */}
      <Card className="p-4 space-y-3">
        <label className="text-sm font-medium">How old is your oldest credit account?</label>
        <Select
          value={data.accountAgeRange}
          onValueChange={(v) => update({ accountAgeRange: v })}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select account age" />
          </SelectTrigger>
          <SelectContent>
            {ACCOUNT_AGE_RANGES.map((r) => (
              <SelectItem key={r.value} value={r.value}>
                {r.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </Card>

      {/* Accounts */}
      <Card className="p-4 space-y-3">
        <label className="text-sm font-medium">Account Summary</label>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-xs text-muted-foreground">Total</label>
            <Input
              type="number"
              min={0}
              value={data.totalAccounts || ""}
              onChange={(e) => update({ totalAccounts: parseInt(e.target.value) || 0 })}
              placeholder="0"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Open</label>
            <Input
              type="number"
              min={0}
              max={data.totalAccounts}
              value={data.openAccounts || ""}
              onChange={(e) => update({ openAccounts: parseInt(e.target.value) || 0 })}
              placeholder="0"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">In Collections</label>
            <Input
              type="number"
              min={0}
              value={data.collectionAccounts || ""}
              onChange={(e) => update({ collectionAccounts: parseInt(e.target.value) || 0 })}
              placeholder="0"
            />
          </div>
        </div>
      </Card>

      {/* Negative Items */}
      <Card className="p-4 space-y-3">
        <label className="text-sm font-medium">Any negative items on your report?</label>
        <div className="grid grid-cols-2 gap-2">
          {NEGATIVE_ITEM_OPTIONS.map((item) => {
            const checked = data.negativeItems.includes(item);
            return (
              <label
                key={item}
                className={cn(
                  "flex items-center gap-2 rounded-md border p-2.5 cursor-pointer text-sm transition-colors",
                  checked ? "border-secondary bg-secondary/5" : "hover:border-muted-foreground/30"
                )}
              >
                <Checkbox
                  checked={checked}
                  onCheckedChange={() => toggleNegativeItem(item)}
                />
                {humanizeLabel(item)}
              </label>
            );
          })}
        </div>
      </Card>
    </div>
  );
}

export { ACCOUNT_AGE_RANGES };
