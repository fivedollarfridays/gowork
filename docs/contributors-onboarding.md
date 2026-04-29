# GoWork — Contributors Onboarding

> **Authored:** W5 Driver D (Spotlight invention).
> **Audience:** New contributors, post-HackFW open-source ramp.
> **Goal:** From "I just cloned this" to "I just shipped a PR" in 30
> minutes. If you finish reading this and you've still got questions,
> open an issue tagged `onboarding-friction` — that's a bug in this
> doc.

---

## In 30 minutes you will

1. Run the Wall locally with a Mapbox token.
2. Run the test suite (~7,500 tests, vitest + pytest).
3. Add a new chapter title in EN + ES, see it propagate.
4. Send your first PR.

---

## Step 0 — Prerequisites (5 min)

- **Node.js** 20+ (tested on 20.18, 22 LTS)
- **Python** 3.13 (3.12 likely works; 3.11 may need `pip` adjustments)
- **Git** any recent version
- **A Mapbox account** — free public token at
  https://account.mapbox.com/access-tokens/. The Wall renders a
  static fallback without it, but the cinematic experience needs the
  real token.
- (Optional) **VS Code** + the recommended extensions in
  `.vscode/extensions.json`. Any editor works.

---

## Step 1 — Clone + install (5 min)

```bash
git clone https://github.com/fivedollarfridays/montgowork.git
cd montgowork

# Frontend
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local — paste your Mapbox token into NEXT_PUBLIC_MAPBOX_TOKEN
npm run dev
# Wall renders at http://localhost:3000
```

```bash
# Backend (separate terminal)
cd backend
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
# API at http://localhost:8000
```

---

## Step 2 — Run the tests (3 min)

```bash
# Frontend
cd frontend
npx vitest run                          # all 3,675+ tests
npx vitest run --watch                  # for development

# Backend
cd backend
python -m pytest tests/ -q              # ~4,080 tests
```

If anything is red on a clean clone, **that's our bug, not yours**.
Open an issue tagged `clean-clone-failure` — they're high priority.

---

## Step 3 — Architecture overview (5 min)

```
montgowork/
├── frontend/                  Next.js 15 app (the Wall + assess + plan)
│   ├── src/
│   │   ├── app/               Next App Router pages
│   │   ├── components/wall/   The 10 Wall chapters (Ch1..Ch10)
│   │   ├── components/        UI components, shared
│   │   ├── lib/wall/          Camera choreography, chapter spec, OG
│   │   ├── lib/translations/  EN + ES locale strings
│   │   ├── hooks/             Reusable React hooks
│   │   └── __tests__/         Vitest test files (mirror of src/)
│   ├── public/                Static assets (OG fallbacks, brand)
│   └── e2e/                   Playwright e2e tests
│
├── backend/                   FastAPI service (assess + plan + RAG)
│   ├── app/
│   │   ├── api/               REST endpoints
│   │   ├── models/            SQLAlchemy ORM
│   │   ├── services/          Business logic
│   │   └── rag/               FAISS vector store + barrier graph DAG
│   └── tests/                 pytest suites
│
├── docs/                      All project documentation
│   ├── press-kit.md           Submission press kit
│   ├── copy-thesis.md         Locked editorial voice (don't paraphrase)
│   ├── visual-rebirth-plan.md The Wall plan + 12 life-layers
│   └── architecture-decisions/ ADRs for major design decisions
│
└── scripts/                   Cross-cutting CLI scripts
```

Read these in order if you want the full picture:

1. `docs/copy-thesis.md` — what we're saying and why.
2. `docs/visual-rebirth-plan.md` — what the Wall is and why it matters.
3. `docs/architecture.md` — system shape + barrier scoring.
4. `docs/architecture-decisions/README.md` — why we chose what we chose.

---

## Step 4 — How to add a new chapter (5 min)

The Wall has 10 chapters. Each one has:

- A React component at
  `frontend/src/components/wall/chapters/Chapter{NN}{Name}.tsx`
- A camera target (lng, lat, zoom, pitch, bearing) in
  `frontend/src/lib/wall/cameraChoreography.ts` `CHAPTER_CAMERAS`
- A chapter spec (slug, sound, title key) in
  `frontend/src/lib/wall/chapterSpec.ts` `CHAPTER_SPECS`
- EN + ES translation entries in
  `frontend/src/lib/translations/en.json` and `es.json`
  under `wall.chapter{NN}.*`
- A test file at
  `frontend/src/components/wall/chapters/__tests__/Chapter{NN}.test.tsx`

**To add an 11th chapter:**

1. Add a new `Chapter11{Name}.tsx` component.
2. Extend `CHAPTER_CAMERAS` and `CHAPTER_SPECS` arrays.
3. Add `wall.chapter11.title`, `wall.chapter11.body`, `wall.chapter11.aria`
   keys to **both** `en.json` and `es.json`.
4. Wire it into `WallContainer.tsx` chapter sequence.
5. Run `npx vitest run src/components/wall/__tests__/walkAllChapters.test.ts` — the walk test will catch any missing config.
6. Run `npx vitest run src/lib/translations/__tests__/translationParity-allW3.test.ts` — parity check fires if EN/ES drift.

The test scaffolds are deterministic. If you forget a translation key,
the parity test tells you exactly which one. If you forget a camera
target, the walk-all-chapters test fails with the chapter index.

---

## Step 5 — How to add a new city (advanced, ~2 hours)

See [`docs/multi-city-expansion-playbook.md`](multi-city-expansion-playbook.md).
Short version: city config + barrier graph + state modules + Mapbox
style + EN/ES translations. The framework is multi-city by
architecture.

---

## Step 6 — Send your first PR (5 min)

1. Branch: `feature/your-thing` or `fix/your-thing` or `docs/your-thing`.
2. **TDD:** write the failing test first (the enforcement layer
   requires it; see `.claude/skills/implementing-with-tdd/SKILL.md`).
3. Make it pass.
4. Run `npx vitest run` + `npx tsc --noEmit` + `npm run lint`.
5. Run `bpsai-pair arch check frontend/` (file size + function count
   limits).
6. PR title: short. PR body: what changed, why, what tests cover it.
7. CI runs all gates. Merge after green.

---

## Conventions

- **File size limits:** source < 400 lines (warning at 200), test
  files < 600 lines (warning at 400). See
  `.claude/rules/architecture.md`.
- **Function limits:** < 50 lines, < 15 functions per file.
- **Editorial voice:** locked in `docs/copy-thesis.md`. Don't
  paraphrase the hero question or the framework tagline.
- **Languages:** EN + ES parity is enforced. Adding a string in EN
  without ES fails parity tests.
- **Reduced motion:** every animated component must respect
  `usePrefersReducedMotion()` and provide a static fallback.
- **A11y:** WCAG AAA contrast everywhere. `npm run contrast` gates.

---

## Where to ask questions

- **GitHub Issues** for bugs, feature requests, onboarding friction
- **GitHub Discussions** for "is this a good idea?" / "how does X work?"
- **r/PairCoder** for community Q&A
- **scsonnet@gmail.com** for direct contact

---

## See also

- [`README.md`](../README.md) — repo root overview
- [`docs/architecture.md`](architecture.md) — full system architecture
- [`docs/architecture-decisions/`](architecture-decisions/) — ADRs
- [`docs/multi-city-expansion-playbook.md`](multi-city-expansion-playbook.md) — adding a new city
- [`docs/visual-rebirth-plan.md`](visual-rebirth-plan.md) — Wall design
- [`.claude/skills/`](../.claude/skills/) — PairCoder skills (TDD, planning, etc.)

---

> **C4 honest uncertainty:** Onboarding times above are estimates from
> a sandbox env. Your first run might be 45 minutes if your Python
> environment fights you, or 15 minutes if you've done this dance
> before. Open an issue if any step took more than 2x its estimate —
> that's where the doc needs sharpening.
