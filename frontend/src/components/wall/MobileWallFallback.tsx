"use client";

/**
 * W4 Driver B — T4.B.9 mobile fallback shell.
 *
 * The cinematic wall (Mapbox + View Transitions + 3D constellation) is
 * not viable on a 360-pixel phone. Instead we ship a static, single-
 * column, editorial-first experience: branded GoWork wordmark + Fort
 * Worth subtitle on top, then 10 chapter cards in scroll order. Each
 * card reads its title and body from the i18n catalog so EN/ES parity
 * is preserved automatically.
 *
 * No Mapbox token check, no WebGL probe, no Three.js — this is the
 * "still image that's still beautiful" path. WallContainer's tier
 * gating already covered low-tier hardware; W4 layers viewport gating
 * on top so judges scouting on phones still see the narrative.
 *
 * The chapter card decomposition (`MobileChapterCard`) lives in this
 * same file because it is single-purpose and only used here. If a
 * future driver needs to re-use the card (e.g. a print-export) they
 * can extract it then.
 */
import { useTranslation } from "@/hooks/useTranslation";

/**
 * Per-chapter copy plan: prefer `body` (the long-form editorial leaf
 * present on chapters 2, 3, 6-10). For chapters 1/4/5 that don't have
 * a `body`, fall back to `subhero` / `lede` / `editorial` in priority
 * order. Each entry pins which leaf to render so we don't accidentally
 * miss content for a chapter.
 */
interface ChapterPlan {
  /** 1..10 — chapter index. */
  id: number;
  /** Localised title key (always `wall.chapter0N.title`). */
  titleKey: string;
  /** Ordered list of body candidates — first non-empty resolution wins. */
  bodyCandidates: readonly string[];
}

const CHAPTERS: readonly ChapterPlan[] = [
  {
    id: 1,
    titleKey: "wall.chapter01.title",
    bodyCandidates: ["wall.chapter01.subhero", "wall.chapter01.editorial"],
  },
  {
    id: 2,
    titleKey: "wall.chapter02.title",
    bodyCandidates: ["wall.chapter02.body", "wall.chapter02.editorial"],
  },
  {
    id: 3,
    titleKey: "wall.chapter03.title",
    bodyCandidates: ["wall.chapter03.body"],
  },
  {
    id: 4,
    titleKey: "wall.chapter04.title",
    bodyCandidates: ["wall.chapter04.lede"],
  },
  {
    id: 5,
    titleKey: "wall.chapter05.title",
    bodyCandidates: ["wall.chapter05.lede", "wall.chapter05.editorial"],
  },
  {
    id: 6,
    titleKey: "wall.chapter06.title",
    bodyCandidates: ["wall.chapter06.body", "wall.chapter06.subhero"],
  },
  {
    id: 7,
    titleKey: "wall.chapter07.title",
    bodyCandidates: ["wall.chapter07.body", "wall.chapter07.subhero"],
  },
  {
    id: 8,
    titleKey: "wall.chapter08.title",
    bodyCandidates: ["wall.chapter08.body", "wall.chapter08.subhero"],
  },
  {
    id: 9,
    titleKey: "wall.chapter09.title",
    bodyCandidates: ["wall.chapter09.body", "wall.chapter09.subhero"],
  },
  {
    id: 10,
    titleKey: "wall.chapter10.title",
    bodyCandidates: ["wall.chapter10.body", "wall.chapter10.subhero"],
  },
];

/** Shorthand: pick the first non-empty translation in a candidate list. */
function pickBody(
  t: (key: string) => string,
  candidates: readonly string[],
): string {
  for (const key of candidates) {
    const value = t(key);
    if (value && value !== key && value.trim().length > 0) return value;
  }
  return "";
}

interface MobileChapterCardProps {
  id: number;
  title: string;
  body: string;
}

function MobileChapterCard({ id, title, body }: MobileChapterCardProps) {
  return (
    <article
      data-testid={`mobile-chapter-card-${id}`}
      data-chapter-id={String(id)}
      className="mb-6 rounded-2xl border border-foreground/10 bg-background/70 p-6 shadow-sm backdrop-blur"
    >
      <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-cyan-400">
        {String(id).padStart(2, "0")} / 10
      </p>
      <h2 className="mb-3 text-xl font-bold tracking-tight">{title}</h2>
      {body ? (
        <p className="text-sm leading-relaxed text-muted-foreground">{body}</p>
      ) : null}
    </article>
  );
}

function MobileHero() {
  const { t } = useTranslation();
  return (
    <header
      className="relative mb-8 flex h-72 flex-col items-center justify-center overflow-hidden rounded-2xl text-center"
      style={{
        background:
          "radial-gradient(ellipse at center, oklch(0.30 0.05 250) 0%, oklch(0.16 0.04 250) 70%)",
        color: "oklch(0.96 0.005 250)",
      }}
    >
      <span
        aria-hidden="true"
        className="absolute inset-0 opacity-30"
        style={{
          backgroundImage:
            "linear-gradient(135deg, transparent 40%, rgba(34, 211, 238, 0.18) 50%, transparent 60%)",
        }}
      />
      <span className="relative z-10 text-4xl font-extrabold tracking-tight">
        GoWork
      </span>
      <span className="relative z-10 mt-1 text-sm opacity-80">
        Fort Worth, TX
      </span>
      <span className="relative z-10 mt-3 max-w-xs text-xs italic opacity-70">
        {t("wall.titleSequence.subtitle")}
      </span>
    </header>
  );
}

/** Top-level mobile fallback shell. */
export function MobileWallFallback(): JSX.Element {
  const { t } = useTranslation();
  return (
    <section
      role="region"
      aria-label={t("wall.titleSequence.title") + " — Fort Worth, TX"}
      data-mobile-wall
      data-testid="mobile-wall-fallback"
      className="mx-auto flex w-full max-w-md flex-col px-4 py-6"
    >
      <MobileHero />
      <div className="flex flex-col">
        {CHAPTERS.map((chapter) => (
          <MobileChapterCard
            key={chapter.id}
            id={chapter.id}
            title={t(chapter.titleKey)}
            body={pickBody(t, chapter.bodyCandidates)}
          />
        ))}
      </div>
    </section>
  );
}
