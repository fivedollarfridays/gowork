"use client";

import { useState, useEffect } from "react";
import { AvailableHours, BarrierType } from "@/lib/types";
import type { BarrierFormData } from "@/components/wizard/BarrierForm";

const DEMO_DATA: BarrierFormData = {
  zipCode: "36104",
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

export function useDemoMode(): BarrierFormData | null {
  const [demoData, setDemoData] = useState<BarrierFormData | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("demo") === "true") {
      setDemoData(DEMO_DATA);
    }
  }, []);

  return demoData;
}
