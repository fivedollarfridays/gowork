/**
 * /dev/wall — chapter inspector (Driver D Spotlight invention #6).
 *
 * Dev-only review surface for the W2 Wall chapters. Lists every chapter
 * with a "jump" link that scrolls the homepage to the chapter's start
 * progress (so reviewers can scrub through narrative beats without
 * scrolling 5×100vh of content). When live data lands (W3+), this page
 * gains a global progress slider.
 *
 * # Why this exists (Compound Lens)
 *
 * Reviewing 5 chapters by manually scrolling burns five minutes per
 * editorial pass. A jump-to-chapter inspector makes a 30-second pass
 * possible. The same surface is W4-friendly (life-layers can be toggled
 * here) and W5-friendly (judges can spot-check each chapter without
 * narrative friction).
 *
 * # Production guard
 *
 * Renders an explicit stub when `NODE_ENV === "production"`. Routing
 * still hits the page but the surface is informational only.
 */
import { CHAPTER_BOUNDS } from "@/lib/wall/wallProgress";
import { CHAPTER_SPECS } from "@/lib/wall/chapterSpec";

const CHAPTER_LABELS: Record<number, string> = {
  1: "Continental",
  2: "City Arrival",
  3: "Neighborhood",
  4: "The Wall",
  5: "Labyrinth",
  // W3 — Driver D updated labels post-merge so reviewers see the actual
  // chapter intent, not a placeholder. Pulled from the chapterSpec slugs.
  6: "The Math (cliff)",
  7: "The Path (5 stops)",
  8: "The Graph (constellation)",
  9: "Any City",
  10: "Find Your Path",
};

function formatCameraSummary(
  cam: ReturnType<typeof Object.values>[number] | undefined,
): string {
  if (!cam || typeof cam !== "object") return "(no camera)";
  const c = cam as {
    longitude: number;
    latitude: number;
    zoom: number;
    pitch: number;
    bearing: number;
  };
  return `lng ${c.longitude.toFixed(2)} · lat ${c.latitude.toFixed(2)} · z${c.zoom} · pitch ${c.pitch}° · bearing ${c.bearing}°`;
}

export default function WallInspectorPage() {
  if (process.env.NODE_ENV === "production") {
    return (
      <main className="mx-auto max-w-3xl px-4 py-12">
        <h1 className="text-2xl font-bold">/dev/wall</h1>
        <p className="mt-2 text-foreground/70">
          Not available in production. Run the dev server.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-12">
      <h1 className="text-3xl font-bold">Wall Inspector</h1>
      <p className="mt-2 text-foreground/70">
        Driver D Spotlight invention #6 — jump-scrub each chapter without
        scrolling the full page. Useful for editorial review + demo
        pre-flight. The chapter index → global-scroll-progress mapping
        comes from <code>lib/wall/wallProgress</code>.
      </p>

      <ul className="mt-8 grid gap-3">
        {CHAPTER_BOUNDS.map((bounds) => {
          const label = CHAPTER_LABELS[bounds.chapter] ?? "(unnamed)";
          const spec = CHAPTER_SPECS.find((s) => s.id === bounds.chapter);
          const startPct = (bounds.start * 100).toFixed(0);
          const endPct = (bounds.end * 100).toFixed(0);
          const jumpHref = `/?scroll=${bounds.start.toFixed(2)}#chapter-${bounds.chapter}`;
          const cameraSummary = formatCameraSummary(spec?.camera);
          const soundLabel = spec?.sound ?? "(silent)";
          return (
            <li
              key={bounds.chapter}
              className="rounded border border-foreground/20 px-4 py-3"
              data-chapter-jump={String(bounds.chapter)}
              data-chapter-slug={spec?.slug ?? "unknown"}
            >
              <div className="flex items-baseline gap-3">
                <span className="font-semibold tabular-nums">
                  Ch {bounds.chapter}
                </span>
                <span>{label}</span>
                <span className="ml-auto text-sm text-foreground/60 tabular-nums">
                  {startPct}% – {endPct}%
                </span>
              </div>
              <div className="mt-1 text-xs text-foreground/60">
                <span data-testid={`ch${bounds.chapter}-camera-summary`}>
                  {cameraSummary}
                </span>
              </div>
              <div className="mt-1 text-xs text-foreground/60">
                <span data-testid={`ch${bounds.chapter}-sound-id`}>
                  Sound: {soundLabel}
                </span>
                {spec?.titleKey ? (
                  <span className="ml-3" data-testid={`ch${bounds.chapter}-title-key`}>
                    titleKey: {spec.titleKey}
                  </span>
                ) : null}
              </div>
              <a
                className="mt-2 inline-block text-sm underline"
                href={jumpHref}
              >
                Jump to start of Ch{bounds.chapter}
              </a>
            </li>
          );
        })}
      </ul>

      <section className="mt-12">
        <h2 className="text-xl font-semibold">Boundary contract</h2>
        <ul className="mt-3 list-disc space-y-1 pl-6 text-sm text-foreground/80">
          <li>
            <code>start</code> is INCLUSIVE — Ch{1}.start = 0.
          </li>
          <li>
            <code>end</code> is EXCLUSIVE for Ch1..9 (so 0.1 belongs to Ch2).
          </li>
          <li>Ch10.end = 1.0 INCLUSIVE so progress=1.0 keeps Ch10 active.</li>
          <li>
            Total chapters: 10 (W3 close: all chapters present, all wired).
          </li>
        </ul>
      </section>
    </main>
  );
}
