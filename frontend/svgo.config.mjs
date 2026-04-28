/**
 * T1.5 — SVGO config for the W1 asset pipeline.
 *
 * Conservative settings: brand-mark SVGs (T1.34 icon.svg, T1.36 og-image.svg,
 * T1.105 chapter-divider.svg, T1.108 barrier-type icons) carry semantic
 * structure that downstream code reads:
 *   - viewBox is required for responsive scaling
 *   - <title> + <desc> back the aria-label / accessible name pipeline
 *   - id attributes are referenced by `<use>` and CSS animations (T1.107)
 *   - named colors map to brand tokens via currentColor / CSS vars
 *
 * Each disabled plugin below is justified inline. SVGO's default plugins
 * remove these aggressively, breaking accessibility / animation behavior.
 *
 * Run: `npm run svgo` (idempotent — runs over public/ recursively).
 */

export default {
  multipass: true,
  js2svg: {
    indent: 2,
    pretty: true,
  },
  plugins: [
    {
      name: "preset-default",
      params: {
        overrides: {
          // viewBox is the contract for responsive SVG sizing — never strip.
          removeViewBox: false,
          // <title> backs aria-label fallback for screen readers.
          removeTitle: false,
          // <desc> provides extended description for assistive tech.
          removeDesc: false,
          // id attributes are referenced by <use> + CSS animation selectors
          // (T1.107 brand-mark hover path-draw needs class="path-draw").
          cleanupIds: false,
          // Inline styles may carry CSS-var references (var(--accent-cyan));
          // converting to attributes can lose the CSS var binding.
          convertStyleToAttrs: false,
        },
      },
    },
  ],
};
