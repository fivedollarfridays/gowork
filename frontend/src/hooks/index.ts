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

export { useVariableFontWeight } from "./useVariableFontWeight";

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
