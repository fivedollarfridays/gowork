"use client";

import { useState, useEffect } from "react";
import { AvailableHours, BarrierType } from "@/lib/types";
import type { BarrierFormData } from "@/components/wizard/BarrierForm";

const DEMO_ZIPS: Record<string, string> = {
  montgomery: "36104",
  "fort-worth": "76102",
};

function getDemoZip(city: string | null): string {
  if (city && city in DEMO_ZIPS) return DEMO_ZIPS[city];
  return DEMO_ZIPS.montgomery;
}

function buildDemoData(city: string | null): BarrierFormData {
  return {
    zipCode: getDemoZip(city),
    employment: "unemployed",
    barriers: {
      [BarrierType.CREDIT]: true,
      [BarrierType.TRANSPORTATION]: true,
      [BarrierType.CHILDCARE]: false,
      [BarrierType.HOUSING]: false,
      [BarrierType.HEALTH]: false,
      [BarrierType.TRAINING]: false,
      [BarrierType.CRIMINAL_RECORD]: false,
    } as Record<BarrierType, boolean>,
    workHistory: "3 years retail experience at Walmart. Cashier and stock associate.",
    hasVehicle: false,
    availableHours: AvailableHours.DAYTIME,
  };
}

export function useDemoMode(): BarrierFormData | null {
  const [demoData, setDemoData] = useState<BarrierFormData | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("demo") === "true") {
      const city = params.get("city");
      setDemoData(buildDemoData(city));
    }
  }, []);

  return demoData;
}
