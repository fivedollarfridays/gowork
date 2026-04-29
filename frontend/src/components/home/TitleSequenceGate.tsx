"use client";

/**
 * TitleSequenceGate — polish-2 T49.
 *
 * Mounts the wall `<TitleSequence>` on first visit only. Subsequent
 * visits (this tab) skip the sequence; `prefers-reduced-motion` users
 * also skip the choreography. When the sequence completes, the gate
 * persists `sessionStorage["gowork-title-seen"] = "1"` so the rest of
 * the session does not see the title bumper again.
 *
 * The actual sequence (1.6s "GoWork presents · The Wall · An interactive
 * map of Fort Worth, Texas") is owned by `wall/TitleSequence.tsx`. This
 * gate only owns the lifecycle decision.
 */
import { useEffect, useState } from "react";
import { TitleSequence } from "@/components/wall/TitleSequence";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";

const SESSION_KEY = "gowork-title-seen";
const DEFAULT_DURATION_MS = 1600;

interface TitleSequenceGateProps {
  /** Override sequence duration (tests pass a small value). */
  durationMs?: number;
}

function readSeen(): boolean {
  if (typeof window === "undefined") return true; // SSR — never render the sequence on the server pass
  try {
    return sessionStorage.getItem(SESSION_KEY) === "1";
  } catch {
    return false;
  }
}

function markSeen(): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(SESSION_KEY, "1");
  } catch {
    /* private browsing — silent no-op */
  }
}

export function TitleSequenceGate({
  durationMs = DEFAULT_DURATION_MS,
}: TitleSequenceGateProps = {}): JSX.Element | null {
  const reduced = usePrefersReducedMotion();
  // Start the gate hidden during SSR; on mount we read sessionStorage
  // and decide. This avoids a hydration mismatch.
  const [show, setShow] = useState<boolean>(false);
  const [decided, setDecided] = useState<boolean>(false);

  useEffect(() => {
    if (reduced) {
      setShow(false);
      setDecided(true);
      return;
    }
    setShow(!readSeen());
    setDecided(true);
  }, [reduced]);

  if (!decided) return null;
  if (!show) return null;
  if (reduced) return null;

  return (
    <TitleSequence
      durationMs={durationMs}
      reducedMotion={reduced}
      onComplete={() => {
        markSeen();
        setShow(false);
      }}
    />
  );
}
