/**
 * W2 Driver C — forward-compatible dependency surface for chapters 4–5.
 *
 * Driver A owns the runtime ChapterScaffold + useChapterProgress (T2.6 / T2.8).
 * Driver B owns the data layers (offices.ts, carlosPath.ts, jobs.ts).
 * Their files do not exist on this branch yet. Driver C must build chapters
 * 4–5 in parallel, so this module declares the SHAPE of what we consume.
 *
 * Strategy:
 *   - Type definitions match the W2 plan's documented contracts.
 *   - A minimal in-tree implementation of each hook/dataset lives here
 *     so chapters render in tests and in dev today.
 *   - When Driver A/B land, the chapters re-import from their canonical
 *     paths and this module shrinks to a `// @deprecated` re-export.
 *
 * NOTHING in this file should leak outside `chapters/`. It is not part of
 * the public Wall API.
 */
import type { ReactNode } from "react";

// ─── ChapterScaffold contract (Driver A — T2.6) ─────────────────────────────
export interface ChapterScaffoldProps {
  /** Logical chapter id, e.g. "04a", "05". Drives narration + analytics. */
  chapterId: string;
  /** Local progress 0..1 inside this chapter (Driver A computes from scroll). */
  progress: number;
  /** Reduced-motion override; null means "consult media query." */
  reducedMotion?: boolean | null;
  /** Editorial overlay + map effects render here. */
  children: ReactNode;
}

// ─── Office layer (Driver B — T2.12) ────────────────────────────────────────
export interface OfficeFeature {
  id: string;
  name: string;
  category: "court" | "transit" | "childcare" | "workforce" | "legal";
  /** Tarrant County coordinates [lon, lat] — pluralized to fit GeoJSON. */
  coords: readonly [number, number];
}

/**
 * Offices used in chapters 4–5. Coordinates are PUBLIC office addresses
 * (not residential), per the PII-safety contract.
 *
 * 4a — Tarrant County District Clerk (criminal record)
 * 4b — Trinity Metro headquarters (no transit)
 * 4c — HHSC Eligibility Office (no childcare)
 * 5  — adds Legal Aid + Workforce Solutions for the Labyrinth
 */
export const W2_OFFICES: readonly OfficeFeature[] = [
  {
    id: "tarrant-district-clerk",
    name: "Tarrant County District Clerk",
    category: "court",
    coords: [-97.3322, 32.7521], // 100 N Calhoun St, Fort Worth
  },
  {
    id: "trinity-metro-hq",
    name: "Trinity Metro",
    category: "transit",
    coords: [-97.3231, 32.7607], // 801 Cherry St
  },
  {
    id: "hhsc-eligibility",
    name: "Texas HHSC Eligibility Office",
    category: "childcare",
    coords: [-97.2895, 32.6886], // E. Berry St area, 76119-adjacent
  },
  {
    id: "legal-aid-nw-texas",
    name: "Legal Aid of NorthWest Texas",
    category: "legal",
    coords: [-97.3308, 32.7498], // 600 E Weatherford St
  },
  {
    id: "workforce-solutions-belknap",
    name: "Workforce Solutions — E. Belknap",
    category: "workforce",
    coords: [-97.2747, 32.7929], // 3210 E Belknap St
  },
] as const;

// ─── Carlos path (Driver B — T2.14) ─────────────────────────────────────────
/**
 * Representative neighborhood coordinate inside ZIP 76119. NOT a residential
 * address — this is a block face / public space marker. PII-safe per T2.28.
 */
export const CARLOS_HOME_PIN: { coords: readonly [number, number] } = {
  coords: [-97.295, 32.696],
} as const;

// ─── Forms catalog (W2 Driver C — Ch5 Labyrinth) ────────────────────────────
/**
 * Real form names referenced in the Labyrinth chapter. Researched for
 * plausibility; the COUNT (47) is the editorial north star, individual
 * names are illustrative of the burden.
 */
export const W2_FORMS: readonly { id: string; agency: string }[] = [
  { id: "DPS CR-09", agency: "Texas DPS" }, // Article 55 expunction
  { id: "HHSC H1010", agency: "HHSC" }, // SNAP / TANF application
  { id: "HHSC H1200", agency: "HHSC" }, // Medicaid renewal
  { id: "HHSC H1014-A", agency: "HHSC" }, // Childcare scholarship intake
  { id: "Legal Aid Intake", agency: "Legal Aid of NW Texas" },
  { id: "DPS DL-43", agency: "Texas DPS" }, // ID renewal
  { id: "TWC WF-1", agency: "Texas Workforce" }, // Workforce registration
] as const;

/** The headline labyrinth count. Source: docs/visual-rebirth-plan.md ch.05. */
export const W2_LABYRINTH_FORM_COUNT = 47;
