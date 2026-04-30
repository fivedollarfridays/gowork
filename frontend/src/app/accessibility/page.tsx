import Link from "next/link";

/**
 * /accessibility — public accessibility statement.
 *
 * Per the W1 brief, the statement commits to WCAG 2.1 AA at minimum,
 * with AAA as the aspirational goal. We list specific surfaces audited
 * (skip-to-content link, ARIA-live region, EN+ES parity, reduced-motion
 * fallbacks for every animation, branded edge states), and we are honest
 * about the surfaces still in-progress (cliff-zone color encoding adds
 * shape redundancy in W4; per-chapter screen-reader narration in W2).
 *
 * No interactivity — pure markup so the page loads with zero JS, ranks
 * cleanly in robots, and is impossible to break with a runtime error.
 */
export const metadata = {
  title: "Accessibility — GoWork",
  description:
    "GoWork's commitment to WCAG 2.1 AA conformance, with AAA as our goal.",
};

export default function AccessibilityPage(): JSX.Element {
  return (
    <main
      id="main"
      role="main"
      className="mx-auto max-w-3xl px-6 py-12 sm:py-16"
    >
      <p className="mb-2 text-xs uppercase tracking-[0.4em] text-[color:var(--accent-cyan)]">
        GoWork
      </p>
      <h1 className="mb-6 text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
        Accessibility statement
      </h1>
      <p className="mb-6 text-lg leading-relaxed text-muted-foreground">
        We believe the wall the worker faces should not extend to the screen
        they read it on. GoWork is built to WCAG 2.1 AA conformance at
        minimum, and we treat WCAG 2.1 AAA as our aspirational goal — not a
        marketing claim, but a target we measure ourselves against.
      </p>

      <h2 className="mt-10 mb-3 text-2xl font-semibold tracking-tight text-foreground">
        What we have shipped
      </h2>
      <ul className="ml-5 list-disc space-y-2 text-muted-foreground">
        <li>
          Skip-to-content link, visible on focus rather than hidden, on every
          page.
        </li>
        <li>
          ARIA-live region scaffolding for chapter announcements and cliff
          warnings.
        </li>
        <li>
          Full English + Spanish parity in the i18n catalog. Spanish is
          translated by the team, not machine-translated; strings under
          cultural review are flagged for navigator-led approval.
        </li>
        <li>
          prefers-reduced-motion is respected at every animation site;
          every camera flight and typewriter has a still-image fallback.
        </li>
        <li>
          Branded 404 / 500 / empty / loading / error states — the wall
          identity reaches the failure modes too.
        </li>
        <li>Tabular-nums on counters so the chapter readout never jitters.</li>
      </ul>

      <h2 className="mt-10 mb-3 text-2xl font-semibold tracking-tight text-foreground">
        What we are still working on
      </h2>
      <ul className="ml-5 list-disc space-y-2 text-muted-foreground">
        <li>
          Color-blind-safe shape redundancy on cliff zones (Sprint W4).
        </li>
        <li>
          Per-chapter screen-reader narration with auto-advance opt-in
          (Sprint W2).
        </li>
        <li>
          Forced-colors mode parity across the Mapbox canvas (Sprint W4).
        </li>
      </ul>

      <h2 className="mt-10 mb-3 text-2xl font-semibold tracking-tight text-foreground">
        Tell us when we miss
      </h2>
      <p className="mb-8 text-muted-foreground">
        If something on GoWork is hard for you to use — a contrast issue, a
        keyboard trap, a screen-reader silence — please open an issue on
        the public repository or email us. We treat accessibility regressions
        as P0 bugs.
      </p>

      <Link
        href="/"
        className="inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        Back to the wall <span aria-hidden="true">→</span>
      </Link>
    </main>
  );
}
