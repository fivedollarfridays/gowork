# T13.77 — ES-Locale Full Platform Sweep

**Sprint:** S13 (sprint/s13-platform-qc)
**Date:** 2026-04-24
**Method:** Playwright (chromium, headless) against
`https://montgowork-staging-web.fly.dev`. Locale set via
`localStorage.setItem("montgowork-locale","es")` then a reload (the i18n
module reads the value at module-init only, so the first navigation always
hydrates in EN — every measurement here is taken from a *second* navigation
where ES is in storage). Two viewports exercised: desktop (1280×720) and
mobile (360×740).

T13.68 already verified static parity: `en.json` and `es.json` both have
308 non-empty keys. T13.77 catches the runtime gaps that static checking
cannot see.

## Summary

| Routes exercised | 10 |
|---|---|
| Routes rendering ES correctly | 5 (`/assess` partially, `/jobs`, `/documents/resume`, `/documents/cover-letters`, `/appointments`) |
| Routes mostly EN under `locale=es` | 5 (`/`, `/daily`, `/plan`, `/credit`, `/case-manager`) |
| Findings — untranslated strings | 6 (one structural, several specific clusters) |
| Findings — copy quality | 1 (missing accents across multiple ES values) |
| Findings — formatting (numbers/dates) | 1 (locale-blind formatting) |
| Findings — i18n template tokens leaking | 0 |
| Findings — layout overflow / clipping (desktop) | 0 |
| Findings — layout overflow / clipping (mobile 360×740) | 0 |
| Horizontal scroll on mobile | None observed |

Net: no broken layouts, no leaked `{{tokens}}` — the runtime issue is
*coverage*, not mechanics. Five of ten top-level routes have substantial
hardcoded English bypassing the `t()` helper entirely. The localStorage-only
locale strategy is also fragile (see Architecture Note).

## Findings

### F-1 (HIGH) — Homepage hero is hardcoded English

- **Route:** `/`
- **Observation:** Hero section renders entirely in English regardless of
  locale — `What's standing between you and a job?`, the marketing
  paragraph (`MontGoWork is a workforce navigator…`), the two CTAs
  (`Get Your Plan`, `Check Credit`), the `How It Works` heading, the
  `STEP 1 / STEP 2 / STEP 3` step labels (`Assess`, `Match`, `Plan`)
  with their descriptions, and `By the Numbers`.
- **Root cause:** `frontend/src/app/page.tsx` lines 58, 62, 69, 72, 82,
  112, plus the `STEPS` array around L25–L30 — all literal strings, no
  `t()` calls. (The header NavBar above this section *is* translated;
  navigation says "Citas / Empleos / Documentos / Resumen diario / Gestor
  de casos" correctly.)
- **Suggested fix:** Add a `home.*` namespace to `en.json`/`es.json`
  (`home.hero_question`, `home.hero_blurb`, `home.cta_plan`,
  `home.cta_credit`, `home.how_heading`, `home.steps[].title`,
  `home.steps[].desc`, `home.numbers_heading`) and migrate `page.tsx` to
  consume them.

### F-2 (HIGH) — `/credit` page is fully untranslated

- **Route:** `/credit`
- **Observation:** Heading `Credit Assessment`, every form label
  (`Credit Score (300-850)`, `Credit Utilization (%)`, `Payment History
  (%)`, `Average Account Age (months)`, `Total Accounts`, `Open
  Accounts`), and the submit button `Assess Credit` are all literal
  English.
- **Root cause:** `frontend/src/app/credit/page.tsx` L44, L49, L65, L73,
  L82, L90 — no `t()` usage on the page.
- **Suggested fix:** Add `credit.*` namespace and wire labels through
  `t()`. Also confirm whether the page is meant to be public — if it is
  the consumer-facing credit assessor, full ES coverage is expected.

### F-3 (HIGH) — `/case-manager` dashboard hero in English

- **Route:** `/case-manager`
- **Observation:** Page renders `Case Manager Dashboard`, the subtitle
  `Aggregate metrics from MontGoWork assessments`, and the empty-state
  `Failed to load dashboard data.` all in English.
- **Root cause:** `frontend/src/app/case-manager/page.tsx` L121, L210,
  L213.
- **Note:** This may be intentional — the case-manager dashboard is the
  advisor view, and the advisor copy elsewhere (e.g. `advisor.inboxHeading`
  "Requiere Atención") *is* in ES, so a partial ES advisor experience
  exists. Recommend treating this as a finding unless product confirms
  case-manager is EN-only.
- **Suggested fix:** Add `caseManager.dashboardTitle`,
  `caseManager.dashboardSubtitle`, `caseManager.loadFailed`.

### F-4 (HIGH) — `/plan` empty-state is English

- **Route:** `/plan` (visited unauthenticated, so empty-state renders)
- **Observation:** `No session ID provided.` and the `Start an
  assessment` CTA link are literal English even though
  `frontend/src/app/plan/page.tsx` is the very page the assess flow
  drops the user onto.
- **Root cause:** `plan/page.tsx` L162, L164.
- **Suggested fix:** Add `plan.empty.noSession` (`No hay sesión`),
  `plan.empty.noToken` (`No se encontró token de acceso`),
  `plan.empty.startCta` (`Iniciar evaluación`).

### F-5 (MED) — `/assess` step indicators are English

- **Route:** `/assess`
- **Observation:** The 7-step progress strip renders in English:
  `Basic Info`, `Resume`, `Barriers`, `Benefits`, `Schedule`,
  `Industries`, `Review & Submit`. The step *bodies* themselves are
  translated (e.g. the title "Cuéntanos sobre ti" — note the missing
  accent — and the description "Responde algunas preguntas…"), but the
  navigation chrome above them is not.
- Additional in-step bleed: `We serve the Montgomery, Alabama area.
  Enter your ZIP code to get started.`, the `ZIP Code` label,
  `Employment Status`, the `Unemployed` option, `I have a vehicle`, and
  the bottom `Next` / `Submit` buttons.
- **Root cause:** `frontend/src/app/assess/page.tsx` — the step `title:`
  fields at L157, L219, L235, L272, L288, L320, L359 are literal strings;
  the ZIP / employment / vehicle labels at L171, L186, L212 are also
  literal. The Next/Submit buttons appear to come from a wizard chrome
  component not yet hooked into `t()`.
- **Suggested fix:** Move step titles into `assess.steps.*` (some
  matching keys like `assess.iHaveVehicle` "Tengo vehiculo" already
  exist — they just aren't being used). Audit the wizard component for
  Next/Back/Submit buttons; route through `common.next` /
  `common.submit` (both keys already exist with correct ES values).

### F-6 (LOW) — Daily session-expired message is fine, but the page is otherwise unobservable

- **Route:** `/daily`
- **Observation:** The unauthenticated render shows only "Sesión
  expirada. Por favor inicia sesión de nuevo." — translated correctly.
  Authenticated rendering of digest sections (`DigestTodaySection`,
  `DigestYesterdaySection`, `DigestWeekSection`, `StallAlert`) was not
  exercised in this sweep because of the auth gate.
- **Suggested follow-up:** A sub-task should run through the same
  digest UI behind a real auth session and re-scan. Components in
  `frontend/src/components/digest/` should be audited.

### F-7 (COPY QUALITY) — Missing accents in several ES strings

ES values appear to have been hand-typed without diacritics in places.
Found by scanning `es.json` for words that should carry accents:

| Key | Current ES | Should be |
|---|---|---|
| `assess.basicInfoTitle` | `Cuentanos sobre ti` | `Cuéntanos sobre ti` |
| `assess.navDesc` | `…obtener tu plan personalizado de reinsercion` | `…reinserción` |
| `assess.iHaveVehicle` | `Tengo vehiculo` | `Tengo vehículo` |
| `assess.scheduleDesc` | `Indicanos tu disponibilidad…` | `Indícanos tu disponibilidad…` |

The rest of `es.json` does use accents correctly (e.g. `Atención`,
`Presentación`, `Categoría`), so this is inconsistency rather than
encoding loss. Reads as machine-typed, not Google-Translate-flat —
copy is otherwise idiomatic. A pass with a Spanish-speaker reviewer or
an automated diacritic-restore tool would clean it up in ~10 minutes.

### F-8 (FORMATTING) — Numbers are locale-blind

- **Route:** `/` (and likely anywhere the `AnimatedCounter` is used)
- **Observation:** Stats render `0.0%` with a US decimal point. ES
  convention is `0,0 %` (comma decimal, space before the percent).
- **Root cause:** `frontend/src/app/page.tsx` passes a `decimals`
  prop that is rendered via `.toFixed()` semantics in
  `AnimatedCounter`. There is no `Intl.NumberFormat` plumbing
  anywhere in the page or counter.
- **Note:** `VersionHistoryList.tsx:26` uses
  `date.toLocaleString(undefined, …)`, which respects the *browser*
  locale but not our app locale — so an `en-US` browser viewing the
  app in `es` mode will still see `Apr 24, 2026`. Pass our app
  locale explicitly.
- **Suggested fix:** Introduce `frontend/src/lib/format.ts` with
  `formatNumber(n, locale)` and `formatDate(d, locale)` wrappers around
  `Intl.NumberFormat('es-ES'|'en-US', …)` and
  `Intl.DateTimeFormat(locale, …)`, drive them from
  `useTranslation().locale`. Track separately from the string-coverage
  fixes; this is a cross-cutting refactor.

## Architecture Note (not a finding, but adjacent)

Locale lives only in `localStorage` under `montgowork-locale`. There is
no cookie, no URL query param, no `Accept-Language` honoring, and no
SSR locale awareness. Implications:

1. **First paint is always English.** Server-rendered HTML is EN; the
   client tree only re-renders ES after hydration reads localStorage.
   Users on slow connections briefly see English before the swap.
2. **Shareable links lose locale.** A user in ES who shares a URL
   with a peer makes the peer click into an EN-rendered page (until
   they too toggle).
3. **Indexability for ES SEO is impossible** — Googlebot has no
   localStorage and will only ever index EN.

If product wants real ES support, T13.77's findings are the surface
fixes; an accompanying spike to migrate to a Next.js i18n routing
strategy (or at minimum a cookie + middleware locale resolver) would
solve the structural side. Worth flagging in S13 retro for backlog.

## Clean Routes (under `locale=es`)

These routes render correctly in ES once hydrated. Mostly because they
short-circuit to a translated empty-state ("No hay sesión disponible.
Inicia una evaluación primero."), so deeper coverage requires an
authenticated sweep.

- `/jobs` — header "Seguimiento de Empleos", empty-state translated
- `/documents/resume` — header "Currículum", empty-state translated
- `/documents/cover-letters` — header "Carta de Presentación",
  empty-state translated
- `/appointments` — header "Citas", empty-state translated

The shell `NavBar` is fully translated on every route
("Citas / Empleos / Documentos / Resumen diario / Gestor de casos") —
that part of the system is solid.

## Copy-Quality Spot Checks

Five randomly drawn keys, judged by a fluent reader on idiomatic
Spanish vs machine-translated bleeding-stiff translation:

| Key | ES value | Verdict |
|---|---|---|
| `common.submit` | "Enviar" | natural |
| `assess.scheduleDesc` | "Indicanos tu disponibilidad para emparejarte con los turnos y opciones de transporte correctos." | natural (modulo missing accent on "Indícanos"); idiomatic phrasing |
| `progressTracker.heading` | "Tu Progreso" | natural |
| `share.sharing` | "Compartiendo..." | natural; appropriate gerund |
| `simulator.benefitsUnlocked` | "Beneficios desbloqueados" | natural; correct technical register |
| `errors.404.cta_home` | "Volver al inicio" | natural; idiomatic |
| `assess.recordTitle` | "Detalles de Antecedentes Penales" | correct legal-register Spanish |
| `advisor.inboxHeading` | "Requiere Atención" | natural |

Verdict: where strings *exist* in ES, they read as written by someone
fluent — not machine-translated. The accent-stripping (F-7) is the
only consistent quality flaw, and it's mechanical, not stylistic.

## Top Issue

**Homepage `/` (F-1)** is the most-broken route. It is the entry point
for every link and every share, and it renders completely in English
under `locale=es` except for the NavBar. A user who clicks the
"Idioma" toggle then bounces back to `/` finds none of the marketing
copy honored their choice. Fix this first.

## Priority Order for Driver Tasks

1. **F-1** Homepage hero (highest visibility, biggest hardcoded surface)
2. **F-4** `/plan` empty-state (the place the assess flow lands)
3. **F-2** `/credit` page (fully untranslated, small surface, easy win)
4. **F-5** `/assess` step labels + Next/Submit (existing keys already
   cover this — just needs wiring)
5. **F-7** Accent restoration in `es.json` (10-minute fix)
6. **F-3** `/case-manager` (verify product intent first)
7. **F-8** Number/date locale formatting (cross-cutting refactor — own
   task)
8. **F-6** Authenticated `/daily` digest sweep (sub-task)

## Method Notes / Limitations

- Sweep ran twice per route — first navigation seeds localStorage, the
  reload re-hydrates the React tree with `locale="es"`. This is the
  best possible client-side simulation of a returning user.
- Auth-gated content was not exercised (`/plan`, `/jobs`,
  `/documents/*`, `/appointments`, `/daily` only show their
  empty-state). A follow-up using the worker-onboarding e2e fixture
  to drive a full assessment then re-render in ES would catch
  `JobCard`, `AppointmentCard`, `DigestTodaySection`, `ResumeSection`,
  and `CoverLetterSection`.
- Layout pass at 360×740 (mobile worst-case) found zero clipping or
  horizontal-scroll on the routes that *do* render ES. If ES coverage
  expands per F-1..F-5, repeat the mobile pass on those newly
  ES-rendered surfaces.
- Sweep scripts were ad-hoc and removed after running; rerunning is a
  ~30-line Playwright file plus one HTTP request per route. If this
  becomes a regression suite, lift it into
  `frontend/e2e/es-locale.spec.ts` with `@locale` tag.

## Time

~30 minutes (15 min: locate i18n mechanism + write sweep; 8 min: run
desktop + mobile sweeps and inspect output; 7 min: cross-reference
findings against source and write report).
