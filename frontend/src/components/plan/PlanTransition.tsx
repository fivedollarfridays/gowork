"use client";

import { useEffect, useState, useCallback } from "react";
import { useReducedMotion } from "framer-motion";
import { Typewriter, ShimmerBar } from "@/lib/motion";

const MESSAGES = [
  "Ready for a new beginning? Let's get you back to work!",
  "Your journey to employment starts right now.",
  "We're building your personalized action plan...",
  "Every step forward matters. You've already taken the first one.",
  "Montgomery has opportunities waiting for you.",
  "You're taking a powerful step toward a brighter future.",
  "Your skills matter. Let's find where they fit.",
  "New doors are about to open. Let's walk through them together.",
];

function pickMessages(): [string, string] {
  const i = Math.floor(Math.random() * MESSAGES.length);
  let j = (i + 1 + Math.floor(Math.random() * (MESSAGES.length - 1))) % MESSAGES.length;
  return [MESSAGES[i], MESSAGES[j]];
}

interface PlanTransitionProps {
  /** Called when the transition is done and plan should be revealed */
  onComplete: () => void;
  /** Set to true once plan data has loaded */
  dataReady: boolean;
}

export function PlanTransition({ onComplete, dataReady }: PlanTransitionProps) {
  const prefersReduced = useReducedMotion();
  const [[msg1, msg2]] = useState(pickMessages);
  const [phase, setPhase] = useState(0); // 0 = first msg, 1 = second msg, 2 = shimmer, 3 = done

  const advance = useCallback(() => {
    setPhase((p) => p + 1);
  }, []);

  // Auto-advance through phases on timers
  useEffect(() => {
    if (prefersReduced) {
      // Skip animations entirely — go straight to done when data is ready
      if (dataReady) onComplete();
      return;
    }

    const timers: ReturnType<typeof setTimeout>[] = [];
    // Phase 0 → 1 after 2.5s (first message lingers)
    timers.push(setTimeout(() => advance(), 2500));
    // Phase 1 → 2 after 5s total (second message lingers)
    timers.push(setTimeout(() => advance(), 5000));
    return () => timers.forEach(clearTimeout);
  }, [prefersReduced, advance, dataReady, onComplete]);

  // Phase 2+ and data ready → complete
  useEffect(() => {
    if (phase >= 2 && dataReady) {
      const t = setTimeout(() => onComplete(), 600);
      return () => clearTimeout(t);
    }
  }, [phase, dataReady, onComplete]);

  if (prefersReduced && !dataReady) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="text-lg text-muted-foreground">Loading your plan...</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center px-4 space-y-8">
      {/* Motivational messages */}
      <div className="max-w-lg space-y-6">
        {phase >= 0 && (
          <h1 className="text-2xl sm:text-3xl font-bold text-primary tracking-tight">
            <Typewriter text={msg1} />
          </h1>
        )}
        {phase >= 1 && (
          <p className="text-lg text-muted-foreground">
            <Typewriter text={msg2} delay={0.2} />
          </p>
        )}
      </div>

      {/* Shimmer loading indicator */}
      <div className="w-full max-w-xs space-y-3">
        <ShimmerBar height="0.375rem" className="rounded-full" />
        {phase < 2 && (
          <p className="text-xs text-muted-foreground animate-pulse">
            Analyzing your profile...
          </p>
        )}
        {phase >= 2 && !dataReady && (
          <p className="text-xs text-muted-foreground animate-pulse">
            Almost there...
          </p>
        )}
        {phase >= 2 && dataReady && (
          <p className="text-xs text-secondary font-medium">
            Your plan is ready!
          </p>
        )}
      </div>
    </div>
  );
}
