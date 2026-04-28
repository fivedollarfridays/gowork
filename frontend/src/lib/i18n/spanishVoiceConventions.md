# GoWork Spanish Voice Conventions

> **Audience**: future drivers adding chapter copy, edge-state strings, or
> any reader-facing text in `frontend/src/lib/translations/es.json`.
>
> **Author**: W4 Driver B (T4.B sprint).

---

## 1. Address the reader as `tú`

GoWork is a worker-first product. Carlos is the reader. We never address
him as a stranger. Every editorial line uses the **informal `tú`** form,
not `usted`.

| Wrong (`usted`)                  | Right (`tú`)                |
| -------------------------------- | --------------------------- |
| "¿Qué le impide conseguir...?"   | "¿Qué te impide...?"        |
| "Comience su evaluación"         | "Comienza tu evaluación"    |
| "Le ayudaremos a..."             | "Te vamos a ayudar a..."    |
| "Recibirá un plan..."            | "Recibirás un plan..."      |

**Why**: pretending the user is a stranger is colder than warm. Carlos
knows what the wall is — we don't need formal distance to prove
expertise.

---

## 2. Brand words and proper nouns stay in English

The following **never translate**, even when the surrounding sentence
is fully Spanish:

| Stays English          | Why                                  |
| ---------------------- | ------------------------------------ |
| GoWork                 | Brand wordmark.                      |
| MIT                    | Brand / license.                     |
| Carlos                 | Personal name.                       |
| Fort Worth             | US city proper noun.                 |
| Montgomery             | US city proper noun.                 |
| Dallas, Houston, etc.  | US city proper nouns.                |
| Trinity Metro          | Transit-system proper noun.          |
| Bus 4 / Bus 6          | Route designators (still English).   |
| Amazon FC DFW5         | Facility code.                       |
| DFW5                   | Facility code (stays as-is).         |
| 76119                  | ZIP code (no localisation).          |
| DPS, HHSC              | TX agency abbreviations.             |
| Workforce Solutions    | Org name (no Spanish equivalent yet).|
| GED, CDL, SNAP         | Program abbreviations (US-locked).   |

**Why**: localising Carlos's name or the bus number breaks the
literal-truth contract — Carlos lives in 76119 and rides Bus 4.
The story is real; the words stay real.

---

## 3. The metaphor lexicon (idiomatic, not literal)

The Wall metaphor is the editorial spine of the site. Spanish users
should hear it the same way English users do — but in Spanish idiom,
not English-syntax-with-Spanish-words.

| Concept           | Spanish phrasing            | Notes                                      |
| ----------------- | --------------------------- | ------------------------------------------ |
| The wall          | el muro                     | Always definite article. Not `la pared`.   |
| The path          | el camino                   | Singular, not `los caminos`.               |
| The math          | las cuentas                 | Plural — "doing the math" → "haciendo las cuentas". |
| The labyrinth     | el laberinto                | Direct cognate, lyrical.                   |
| The graph (Ch8)   | el grafo                    | NOT `la gráfica` (which means "chart").    |
| The cliff (Ch6)   | el precipicio               | Editorial register; `el acantilado` works in API/legal copy. |
| Resolve a barrier | resolver una barrera        | Not `arreglar` (too utilitarian).          |
| Sequence the path | ordenar el camino           | Not `secuenciar` (too technical).          |
| Step / first step | paso / primer paso          | Always singular, lyrical.                  |
| Plan              | plan                        | Cognate, no translation needed.            |
| Get unstuck       | destrabar                   | Active verb, not `desbloquear`.            |

---

## 4. Voice register: editorial vs. utility

The editorial chapters (the Wall narrative) and the utility surfaces
(forms, legal pages, API errors) speak slightly differently.

### Editorial register

**Short, lyrical, sentence-fragments-allowed.** Mirrors the English
chapter copy. Example (Ch6):

> EN: "Cuando ganar más significa tener menos."
>
> ES: "Cuando ganar más significa tener menos."

That's a near-direct translation — and it lands the rhythm. Don't add
"En realidad," or "Lo que pasa es que" prefixes that water it down.

### Utility register

**Plain, complete sentences, no punching.** Used for forms, legal,
edge-state pages, and admin surfaces. Example (privacy):

> EN: "We collect only what we need to run the service. Specifically:"
>
> ES: "Solo recopilamos lo necesario para operar el servicio. En concreto:"

Both registers use `tú`.

---

## 5. Number, currency, date formats

| Item        | EN                | ES                       |
| ----------- | ----------------- | ------------------------ |
| Currency    | $1,200            | 1,200 dólares            |
| Currency (compact) | $1,200/mo  | $1,200/mes               |
| Time        | 71 minutes        | 71 minutos (NOT minute)  |
| Time (abbrev) | 71 min          | 71 min (same)            |
| Percentage  | 33%               | 33%                      |
| Date        | April 2026        | abril de 2026            |
| ZIP code    | 76119             | 76119 (no localisation)  |
| Phone       | (817) 555-...     | (817) 555-... (no change)|

**Decimal separator**: keep the EN convention (period for decimals,
comma for thousands) — financial data flows from US sources and we
don't want to introduce a parsing surface.

---

## 6. Approved idiomatic substitutions

These are flagged so a future native reviewer can swap them with one
edit if a stronger phrasing exists. Each is currently shipped:

| Key | EN | Current ES | Alt ES (if reviewer prefers) |
| --- | --- | --- | --- |
| `wall.chapter04a.pullquote` | "I came home with $300 and a daughter, and the system told me to go to five offices." | "Volví a casa con 300 dólares y una hija, y el sistema me mandó a cinco oficinas." | "...y el sistema me mandó a recorrer cinco oficinas." |
| `wall.chapter04b.pullquote` | "Forty-five minutes is the schedule. Eighty-seven is the day." | "Cuarenta y cinco minutos es el horario. Ochenta y siete es el día." | (lyrical-fine) |
| `wall.chapter04d.pullquote` | "A score I can't see is closing doors I never knocked on." | "Un puntaje que no veo me está cerrando puertas a las que nunca toqué." | "...puertas que ni siquiera toqué." |
| `wall.chapter07.body` | "Trinity Metro Bus 4 and Bus 6 carry him between them." | "Los autobuses 4 y 6 de Trinity Metro lo llevan entre una y otra." | "...lo llevan de una a otra." |
| `wall.chapter08.subhero` | "Resolve one and three others move within reach." | "Resuelves una y otras tres se acercan." | "...y otras tres quedan a tu alcance." |

**Honest uncertainty (C5)**: any of these can be improved by a true
native reviewer. The swap is one-line per key.

---

## 7. Common pitfalls to avoid

### Don't translate proper nouns

✗ "Distrito de Ciudad" instead of "Trinity Metro"
✓ "Trinity Metro"

### Don't gender-flip the reader

The reader is `tú` (gender-neutral). Avoid adjectives that pick a
gender ("listo" vs "lista") for second-person address. Prefer
gender-neutral phrasings or rotate forms across the catalog.

✗ "Estás listo para empezar" (assumes male)
✓ "¿Listo para empezar?" (less assumed) OR "¿Empezamos?"

### Don't use machine-translation rhythms

Google Translate writes "el sistema te dijo a ir" — broken syntax.
Always have a fluent reader review.

### Don't break the EN/ES key parity

Every key in `en.json` MUST exist in `es.json` (mechanically enforced
by `frontend/src/lib/i18n/__tests__/missingKeysAudit.test.ts`). If you
add a key in EN, add it in ES in the same commit.

### Don't ship `[ES-pending-review]` flags

Same audit test asserts no leaf carries the `[ES-pending-review]`
marker. Use the marker DURING drafting, but resolve it before merge.

---

## 8. Allowlisted byte-identical pairs

A small set of EN/ES leaves are intentionally identical (proper nouns,
single-character negatives, abbreviated units, brand wordmarks). They
live in `IDENTICAL_PAIR_ALLOWLIST` inside
`backend/tests/test_i18n_completeness.py`. If you add an identical
pair, document it there with rationale.

---

## 9. Test contract (machine-checkable)

Three tests guard the catalog:

1. **Set diff** — `frontend/src/lib/i18n/__tests__/missingKeysAudit.test.ts`
   asserts every key in `en.json` has a counterpart in `es.json`.
2. **No flags** — same test asserts no `[ES-pending-review]` markers leak.
3. **Allowlist** — `backend/tests/test_i18n_completeness.py` rejects
   byte-identical EN/ES pairs unless allowlisted with rationale.

If you violate any of these, CI will block the merge.

---

## 10. Reviewer escalation

If you hit a string where best-judgment Spanish doesn't feel right
(register mismatch, regional idiom doubt, gender ambiguity), flag it
with a line comment in your PR — the W4 driver and a native-fluent
reviewer will pair on it. **Do not** ship `[ES-pending-review]` to
main; either resolve in the PR or remove the key.
