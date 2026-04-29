/**
 * OKLCH → sRGB hex converter for Mapbox GL paint properties.
 *
 * Mapbox GL JS only parses hex / rgb() / rgba() / hsl() / hsla() / named colors.
 * Our design tokens are OKLCH (W1 contract). Layer paint properties that
 * embed OKLCH literals crash at register time with "color expected".
 */

function srgbCompand(x: number): number {
  const sign = x < 0 ? -1 : 1;
  const abs = Math.abs(x);
  return abs <= 0.0031308
    ? sign * 12.92 * abs
    : sign * (1.055 * Math.pow(abs, 1 / 2.4) - 0.055);
}

function clampByte(v: number): number {
  return Math.round(Math.max(0, Math.min(1, v)) * 255);
}

function toHexPair(v: number): string {
  return v.toString(16).padStart(2, "0");
}

/** Convert OKLCH(L C H) to a "#RRGGBB" hex string Mapbox can consume. */
export function oklchToHex(l: number, c: number, h: number): string {
  const hRad = (h * Math.PI) / 180;
  const a = c * Math.cos(hRad);
  const b = c * Math.sin(hRad);

  const lPrime = l + 0.3963377774 * a + 0.2158037573 * b;
  const mPrime = l - 0.1055613458 * a - 0.0638541728 * b;
  const sPrime = l - 0.0894841775 * a - 1.291485548 * b;

  const L = lPrime ** 3;
  const M = mPrime ** 3;
  const S = sPrime ** 3;

  const rLin = 4.0767416621 * L - 3.3077115913 * M + 0.2309699292 * S;
  const gLin = -1.2684380046 * L + 2.6097574011 * M - 0.3413193965 * S;
  const bLin = -0.0041960863 * L - 0.7034186147 * M + 1.7076147010 * S;

  const r = clampByte(srgbCompand(rLin));
  const g = clampByte(srgbCompand(gLin));
  const bChan = clampByte(srgbCompand(bLin));

  return `#${toHexPair(r)}${toHexPair(g)}${toHexPair(bChan)}`;
}

/**
 * Pre-computed Mapbox-safe hex equivalents of the W2/W3 layer colors.
 * Use these in Mapbox layer paint properties instead of the OKLCH literals.
 * Source-of-truth lives in `app/styles/tokens/colors.css`.
 */
export const MAPBOX_COLORS = {
  amber: oklchToHex(0.78, 0.16, 75),
  amberStrong: oklchToHex(0.86, 0.18, 80),
  cyan: oklchToHex(0.78, 0.13, 215),
  mutedGray: oklchToHex(0.52, 0.02, 250),
  skyDeep: oklchToHex(0.18, 0.04, 270),
} as const;
