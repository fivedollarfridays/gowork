"use client";

import { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { getBarrierSequence, simulateBarriers } from "@/lib/api";
import { BarrierSequenceViz, type BarrierSequenceData } from "./BarrierSequenceViz";
import { WhatHappensIf, type SimulationResults } from "./WhatHappensIf";

interface Props {
  sessionId: string;
  token: string;
  barriers: string[];
}

/**
 * Plan insights panel: barrier sequence visualization + "What Happens If" simulator.
 * Loaded on the plan page below barrier cards.
 */
export function PlanInsights({ sessionId, token, barriers }: Props) {
  const [simResults, setSimResults] = useState<SimulationResults | undefined>();

  const { data: sequence } = useQuery<BarrierSequenceData>({
    queryKey: ["barrier-sequence", sessionId, token],
    queryFn: () => getBarrierSequence(sessionId, token),
    enabled: !!sessionId && !!token && barriers.length > 0,
  });

  const handleSimulate = useCallback(
    async (resolved: string[]) => {
      try {
        const result = await simulateBarriers(sessionId, resolved, token);
        setSimResults(result as SimulationResults);
      } catch {
        // Silently fail -- simulator is non-critical
      }
    },
    [sessionId, token],
  );

  if (barriers.length === 0) return null;

  return (
    <div className="space-y-4">
      {sequence && <BarrierSequenceViz sequence={sequence} />}
      <WhatHappensIf
        barriers={barriers}
        onSimulate={handleSimulate}
        simulationResults={simResults}
      />
    </div>
  );
}
