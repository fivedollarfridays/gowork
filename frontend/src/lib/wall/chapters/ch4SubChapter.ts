/**
 * W2 Driver C — Chapter 4 sub-chapter state machine (T2.31).
 *
 * Chapter 4 names FOUR walls one at a time. Each lives 25% of the chapter:
 *   0.00 ≤ p < 0.25  → 4a — criminal record
 *   0.25 ≤ p < 0.50  → 4b — no transit
 *   0.50 ≤ p < 0.75  → 4c — no childcare
 *   0.75 ≤ p ≤ 1.00  → 4d — bad credit
 *
 * Progress is the LOCAL value 0..1 inside chapter 4 — Driver A's
 * `useChapterProgress` produces it from the global scroll position.
 *
 * `barrier` keys are namespaced for translations:
 *   wall.chapter04a.title   "Criminal record"
 *   wall.chapter04a.detail  "4.8 miles. Bus 4 + Bus 6 = 71 minutes."
 *   wall.chapter04a.statValue "71 min"
 */
import { W2_OFFICES } from "./deps";

export type Ch4SubChapterId = "4a" | "4b" | "4c" | "4d";

export interface Ch4SubChapter {
  id: Ch4SubChapterId;
  /** i18n key suffix — combine with `wall.chapter04{id}` to render. */
  barrier: string;
  /** Stat band value, locked from the plan file. */
  statValue: string;
  /** Office id (from W2_OFFICES) the sub-chapter highlights. Empty for 4d. */
  highlightOfficeId: string;
  /** Camera bearing offset for sub-chapter (degrees from chapter base). */
  bearingOffset: number;
  /** Sound id (mapped to existing sound catalog at runtime). */
  soundId: "paper-rustle" | "footstep" | "calculator-click";
}

export const CH4_SUBCHAPTERS: readonly Ch4SubChapter[] = [
  {
    id: "4a",
    barrier: "criminalRecord",
    statValue: "71 min",
    highlightOfficeId: "tarrant-district-clerk",
    bearingOffset: 0,
    soundId: "paper-rustle",
  },
  {
    id: "4b",
    barrier: "noTransit",
    statValue: "87 min",
    // Wave 5 (Driver D): aligned to Driver B's officeRegistry. The "no
    // transit" sub-chapter highlights the DPS office — the long-bus-ride
    // destination Carlos must reach for ID renewal + license reinstatement.
    highlightOfficeId: "tx-dps-mega-center-fort-worth",
    bearingOffset: 30,
    soundId: "footstep",
  },
  {
    id: "4c",
    barrier: "noChildcare",
    statValue: "$1,200/mo",
    // Wave 5 (Driver D): aligned to Driver B's officeRegistry id for the
    // HHSC benefits office (handles childcare scholarship intake referenced
    // in Ch4c per the demo script).
    highlightOfficeId: "hhsc-fort-worth-east-lancaster",
    bearingOffset: -15,
    soundId: "paper-rustle",
  },
  {
    id: "4d",
    barrier: "badCredit",
    statValue: "33%",
    highlightOfficeId: "",
    bearingOffset: -30,
    soundId: "calculator-click",
  },
] as const;

const BOUNDARIES: readonly number[] = [0.25, 0.5, 0.75];

/** Map LOCAL chapter progress (0..1) to the active sub-chapter id. */
export function ch4SubChapter(progress: number): Ch4SubChapterId {
  const p = Math.max(0, Math.min(1, progress));
  if (p < BOUNDARIES[0]) return "4a";
  if (p < BOUNDARIES[1]) return "4b";
  if (p < BOUNDARIES[2]) return "4c";
  return "4d";
}

/** Look up the sub-chapter record by id. */
export function getCh4SubChapter(id: Ch4SubChapterId): Ch4SubChapter {
  const found = CH4_SUBCHAPTERS.find((s) => s.id === id);
  if (!found) throw new Error(`Unknown ch4 sub-chapter: ${id}`);
  return found;
}

/** Look up the highlighted office record (or null for 4d). */
export function getCh4HighlightOffice(id: Ch4SubChapterId) {
  const sub = getCh4SubChapter(id);
  if (!sub.highlightOfficeId) return null;
  return W2_OFFICES.find((o) => o.id === sub.highlightOfficeId) ?? null;
}
