/**
 * tempMultiplier — typed CSS-token wiring for `--temperature-multiplier`.
 *
 * W3 Driver A — Spotlight invention #1.
 *
 * # Why this exists
 *
 * The W1 token `--temperature-multiplier` lives at `:root` in
 * `app/styles/tokens/colors.css` and drives `--accent-current` via a
 * `color-mix(...)` between cyan (cool) and rose (hot). W3 Ch6 (cliff
 * math) needs to drive that token from a wage slider — and W4 cliff
 * proximity tints will read the same property at chapter scope.
 *
 * Without a typed module, three chapters would each invent their own
 * `element.style.setProperty('--temperature-multiplier', String(x))`
 * arithmetic. The wage→multiplier formula would drift between chapters.
 * Honest uncertainty would compound.
 *
 * # Contract
 *
 * - Wages are clamped to [MIN_WAGE_USD, MAX_WAGE_USD].
 * - Multipliers are clamped to [MIN_MULTIPLIER, MAX_MULTIPLIER].
 * - Setting works on `document.documentElement` by default; passing a
 *   scoped element overrides only that subtree (used by Ch6 to keep the
 *   slider's local effect from poisoning the rest of the page).
 *
 * # Spotlight Lens
 *
 * Compound (W3→W4): Ch7's cliff-warning ripple uses the same setter when
 * a job hover puts Carlos within $1/hr of a known cliff. Wisdom: the
 * arithmetic is one place, not three.
 */

/** Federal minimum wage as of 2026 — also the slider's lower bound. */
export const MIN_WAGE_USD = 7.25 as const;

/** Slider upper bound — above this the cliff fades for Carlos's family. */
export const MAX_WAGE_USD = 25 as const;

/** Multiplier value when no cliff pressure is present. */
export const MIN_MULTIPLIER = 1.0 as const;

/** Multiplier value at the deepest cliff Carlos can hit in this range. */
export const MAX_MULTIPLIER = 2.5 as const;

/** Canonical CSS custom-property name. Matches `colors.css`. */
export const TEMP_MULTIPLIER_PROPERTY = "--temperature-multiplier" as const;

function clamp(value: number, min: number, max: number): number {
  if (Number.isNaN(value)) return min;
  if (value < min) return min;
  if (value > max) return max;
  return value;
}

/** Linear map from wage (USD/hr) to temperature-multiplier. */
export function wageToMultiplier(wage: number): number {
  const w = clamp(wage, MIN_WAGE_USD, MAX_WAGE_USD);
  const wageSpan = MAX_WAGE_USD - MIN_WAGE_USD;
  const multSpan = MAX_MULTIPLIER - MIN_MULTIPLIER;
  return MIN_MULTIPLIER + ((w - MIN_WAGE_USD) / wageSpan) * multSpan;
}

/** Inverse — given a multiplier, recover the wage that produced it. */
export function multiplierToWage(multiplier: number): number {
  const m = clamp(multiplier, MIN_MULTIPLIER, MAX_MULTIPLIER);
  const wageSpan = MAX_WAGE_USD - MIN_WAGE_USD;
  const multSpan = MAX_MULTIPLIER - MIN_MULTIPLIER;
  return MIN_WAGE_USD + ((m - MIN_MULTIPLIER) / multSpan) * wageSpan;
}

/**
 * Set the temperature-multiplier custom property.
 *
 * @param value Multiplier; clamped to [MIN_MULTIPLIER, MAX_MULTIPLIER].
 * @param scope Optional element scope. Defaults to document.documentElement.
 */
export function setTemperatureMultiplier(
  value: number,
  scope?: HTMLElement,
): void {
  if (typeof document === "undefined") return;
  const target = scope ?? document.documentElement;
  if (!target) return;
  const clamped = clamp(value, MIN_MULTIPLIER, MAX_MULTIPLIER);
  target.style.setProperty(TEMP_MULTIPLIER_PROPERTY, String(clamped));
}

/** Read the current temperature-multiplier; returns MIN_MULTIPLIER when unset. */
export function readTemperatureMultiplier(scope?: HTMLElement): number {
  if (typeof document === "undefined") return MIN_MULTIPLIER;
  const target = scope ?? document.documentElement;
  if (!target) return MIN_MULTIPLIER;
  const inline = target.style.getPropertyValue(TEMP_MULTIPLIER_PROPERTY);
  if (inline) {
    const parsed = parseFloat(inline);
    if (Number.isFinite(parsed)) return parsed;
  }
  return MIN_MULTIPLIER;
}
