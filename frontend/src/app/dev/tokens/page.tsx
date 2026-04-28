/**
 * /dev/tokens — token gallery (T1.76).
 *
 * Dev-only inventory of every visual token the Wall ships:
 *   - Color: hex + OKLCH swatches with WCAG contrast pairs
 *   - Typography: fluid type scale at min/max
 *   - Motion: spring + easing + duration tokens
 *   - Brand: BrandMark at 16/32/192/512px sizes
 *   - Z-Stack: overlay hierarchy (Wave 2)
 *
 * Production guard: renders a "Not available in production" stub when
 * NODE_ENV === "production". Use only in dev (Vercel preview, local).
 */
import { BrandMark } from "@/components/wall/BrandMark";
import {
  SPRING_SOFT,
  SPRING_SNAPPY,
  SPRING_ELASTIC,
  EASE_LINEAR_SIG,
  EASE_OUT,
  DURATION_BASELINE_MS,
  STAGGER_CHILD_OFFSET_S,
  FONT_AXES,
} from "@/lib/wall/tokens";
import { TokenSection } from "./_sections";

export default function TokensPage() {
  if (process.env.NODE_ENV === "production") {
    return (
      <main className="mx-auto max-w-3xl px-4 py-12">
        <h1 className="text-2xl font-bold">/dev/tokens</h1>
        <p className="mt-2 text-foreground/70">
          Not available in production. Run the dev server.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-12">
      <header className="mb-8 border-b border-foreground/10 pb-4">
        <h1 className="text-3xl font-extrabold tracking-tight">
          GoWork Tokens
        </h1>
        <p className="mt-1 text-sm text-foreground/70">
          Single-source token inventory. Hex + OKLCH swatches, fluid type
          scale, motion springs, brand mark sizes, z-stack hierarchy. Dev-only
          surface; production 404s.
        </p>
      </header>

      <TokenSection
        title="Color"
        items={[
          { name: "--bg-base", value: "#0A0E1A" },
          { name: "--bg-surface", value: "#0F1729" },
          { name: "--bg-elevated", value: "#1A2338" },
          { name: "--fg-primary", value: "#F5F3EE" },
          { name: "--fg-secondary", value: "#A4B3C7" },
          { name: "--fg-muted", value: "#8696A8" },
          { name: "--accent-cyan", value: "#22D3EE" },
          { name: "--accent-amber", value: "#F59E0B" },
          { name: "--accent-rose", value: "#FB7185" },
        ]}
        renderRow={(item) => (
          <div className="flex items-center gap-3">
            <span
              aria-hidden="true"
              className="inline-block h-8 w-8 rounded border border-foreground/10"
              style={{ background: item.value }}
            />
            <code>{item.name}</code>
            <span className="text-foreground/60">{item.value}</span>
          </div>
        )}
      />

      <TokenSection
        title="Typography"
        items={[
          { name: "--type-display", value: "clamp(3rem, 2rem + 5vw, 6.5rem)" },
          { name: "--type-h1", value: "clamp(2rem, 1.4rem + 3vw, 4rem)" },
          { name: "--type-h2", value: "clamp(1.5rem, 1.2rem + 1.5vw, 2.5rem)" },
          { name: "--type-h3", value: "clamp(1.25rem, 1rem + 1vw, 1.75rem)" },
          { name: "--type-body", value: "clamp(1rem, 0.9rem + 0.5vw, 1.25rem)" },
          { name: "--type-small", value: "clamp(0.875rem, 0.85rem + 0.25vw, 1rem)" },
        ]}
        renderRow={(item) => (
          <div>
            <code className="text-foreground/80">{item.name}</code>
            <div className="text-foreground/60">{item.value}</div>
          </div>
        )}
      />

      <TokenSection
        title="Motion"
        items={[
          { name: "SPRING_SOFT", value: JSON.stringify(SPRING_SOFT) },
          { name: "SPRING_SNAPPY", value: JSON.stringify(SPRING_SNAPPY) },
          { name: "SPRING_ELASTIC", value: JSON.stringify(SPRING_ELASTIC) },
          { name: "EASE_LINEAR_SIG", value: JSON.stringify(EASE_LINEAR_SIG) },
          { name: "EASE_OUT", value: JSON.stringify(EASE_OUT) },
          { name: "DURATION_BASELINE_MS", value: `${DURATION_BASELINE_MS}ms` },
          { name: "STAGGER_CHILD_OFFSET_S", value: `${STAGGER_CHILD_OFFSET_S}s` },
        ]}
        renderRow={(item) => (
          <div className="flex items-baseline gap-3">
            <code className="text-foreground/80">{item.name}</code>
            <span className="text-foreground/60">{item.value}</span>
          </div>
        )}
      />

      <TokenSection
        title="Font Axes"
        items={Object.entries(FONT_AXES).map(([k, v]) => ({
          name: `FONT_AXES.${k}`,
          value: String(v),
        }))}
        renderRow={(item) => (
          <div className="flex items-baseline gap-3">
            <code>{item.name}</code>
            <span className="text-foreground/60">{item.value}</span>
          </div>
        )}
      />

      <TokenSection
        title="Brand Mark — sizes"
        items={[
          { name: "16px", value: 16 },
          { name: "32px", value: 32 },
          { name: "192px", value: 192 },
          { name: "512px", value: 512 },
        ]}
        renderRow={(item) => (
          <div className="flex items-center gap-3">
            <BrandMark size={item.value as number} />
            <span className="text-foreground/60">{item.name}</span>
          </div>
        )}
      />

      <TokenSection
        title="Z-Stack hierarchy"
        items={[
          { name: "--z-skip-link", value: "100" },
          { name: "--z-modal", value: "80" },
          { name: "--z-toast", value: "70" },
          { name: "--z-header", value: "50" },
          { name: "--z-banner", value: "40" },
          { name: "--z-pwa-prompt", value: "30" },
          { name: "--z-cookie", value: "30" },
          { name: "--z-cursor-flashlight", value: "5" },
          { name: "--z-content", value: "1" },
        ]}
        renderRow={(item) => (
          <div className="flex items-baseline gap-3">
            <code className="text-foreground/80">{item.name}</code>
            <span className="text-foreground/60">{item.value}</span>
          </div>
        )}
      />
    </main>
  );
}
