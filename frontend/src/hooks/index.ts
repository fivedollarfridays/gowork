/**
 * Hooks barrel (T1.69).
 *
 * Re-exports all W1 utility hooks plus the legacy hooks the app already
 * relied on (so existing direct imports still work). Allows
 * `import { useTimeOfDay, useCursorPosition } from "@/hooks"`.
 */

// W1 utility hooks (T1.24–T1.33)
export { useTimeOfDay } from "./useTimeOfDay";
export type { TimePhase, AccentShift, TimeOfDayState } from "./useTimeOfDay";

export { useCursorPosition } from "./useCursorPosition";
export type { CursorPosition } from "./useCursorPosition";

export { useLiveNow } from "./useLiveNow";
export type { LiveNowState } from "./useLiveNow";

export { useScrollProgress } from "./useScrollProgress";
export type { ScrollProgressState } from "./useScrollProgress";

// W2 hook — sticky-pin escape hatch for chapter scaffolds (T2.10).
export { useScrollPin } from "./useScrollPin";
export type { ScrollPinState } from "./useScrollPin";

// W2 hook — chapter-aware progress derived from useScrollProgress (T2.8).
export { useChapterProgress } from "./useChapterProgress";
export type { ChapterProgressState } from "./useChapterProgress";

export { useVariableFontWeight } from "./useVariableFontWeight";
// W4 — hero + chapter-heading variants (T4.A.6).
export {
  useHeroFontWeight,
  useChapterHeadingFontWeight,
} from "./useHeroFontWeight";

// W4 — Mapbox sky setter (T4.A.1) and rAF throttler (Spotlight #2).
export { useMapboxSkyForTimeOfDay } from "./useMapboxSkyForTimeOfDay";
export type { MapLike } from "./useMapboxSkyForTimeOfDay";
export { useThrottledRAF } from "./useThrottledRAF";
// W4 — locale-aware Live Now formatter (T4.A.4).
export { useLiveNowFormatted } from "./useLiveNowFormatted";
export type { LiveNowFormattedState } from "./useLiveNowFormatted";

export { useScrollVelocity } from "./useScrollVelocity";
export type { ScrollVelocityState } from "./useScrollVelocity";

export { usePrefersReducedMotion } from "./usePrefersReducedMotion";
export { useIdleState } from "./useIdleState";
export { useViewTransitionsSupport } from "./useViewTransitionsSupport";

export {
  useLanguage,
  GOWORK_LOCALE_KEY,
  LEGACY_LOCALE_KEY,
} from "./useLanguage";
export type { UseLanguageResult } from "./useLanguage";

// Legacy hooks (kept here so consumers can use a single import root).
export { useTranslation, TranslationProvider } from "./useTranslation";
export { useCityConfig } from "./useCityConfig";
export type { CityConfig, CityConfigResult } from "./useCityConfig";
