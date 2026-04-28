# Spanish Translation Review Checklist

> Wave 2 — Cross-driver integration  
> Status: pending native-Spanish reviewer pass (Carlos / Spanish-speaker auditor)

## Scope

This checklist covers the four highest-impact Spanish strings the Wall renders. Any judge or visitor who lands on a 404, 500, or first-load surface in `es-MX` / `es-US` reads these strings BEFORE they read any chapter copy. They MUST land formal-but-warm, never machine-translated.

A reviewer who is a native Spanish speaker (preferably Texan / Mexican-American to match Fort Worth's demographic) should walk through each string and answer the prompts.

If any answer is "no" → flag for revision in W4 Spanish-parity pass.

---

## String 1 — 404 wall metaphor

**Source key:** `wall.404.title` + `wall.404.body` + `wall.404.cta`

**English:**
> No path to this URL — but there is one through the wall. Every barrier connects to the next — let's get you back on the path.  
> CTA: Back to the wall

**Spanish:**
> No hay un camino hacia esta dirección. Pero sí hay uno a través del muro. Cada barrera se conecta con la siguiente — vamos a regresarte a la ruta.  
> CTA: Volver al muro

**Reviewer prompts:**

- [ ] Does "No hay un camino hacia esta dirección" land as a missed path (not a missing physical address)?
- [ ] Does "a través del muro" preserve the wall metaphor without sounding like a literal traversal of bricks?
- [ ] Does "vamos a regresarte a la ruta" feel formal-but-warm? Or does the "vamos" diminutive read juvenile?
- [ ] Should it be "tu ruta" instead of "la ruta" to keep ownership warm?
- [ ] Spanish punctuation: confirm the em-dash matches editorial style (no double-spacing).

## String 2 — 500 calibrating motif

**Source key:** `wall.500.title` + `wall.500.body` + `wall.500.cta`

**English:**
> Something stopped. We are recalibrating. The page hit an error, our team was notified, and the request is logged. Try again, or head home.  
> CTA: Try again

**Spanish:**
> Algo se detuvo. Estamos recalibrando. La página tropezó con un error, nuestro equipo fue notificado y la solicitud quedó registrada. Inténtalo de nuevo, o regresa al inicio.  
> CTA: Intentar de nuevo

**Reviewer prompts:**

- [ ] Does "tropezó con un error" preserve the calibrating-system metaphor (something stumbled, not crashed)?
- [ ] Is "Inténtalo de nuevo" the right register, or should it be "Vuelve a intentarlo" / "Intentar nuevamente"?
- [ ] "regresa al inicio" — formal enough? Or does "vuelve al inicio" read warmer?
- [ ] Tone: does the message sound apologetic-but-confident (not panicked)?

## String 3 — Footer brand label / tagline

**Source key:** `footer.brand.label` and any tagline strings

**English:**
> GoWork — workforce infrastructure for any American city.

**Spanish (current):** _check `frontend/src/lib/translations/es.json` for the actual rendered string_

**Reviewer prompts:**

- [ ] Does the Spanish form preserve "infrastructure for any city" without sounding bureaucratic?
- [ ] Should "American" map to "estadounidense" or be omitted (since the product is city-agnostic)? Recommendation: drop "American" in Spanish to avoid nationalism framing for a Mexican-American audience.
- [ ] Does the sentence keep the same rhythm (short, declarative)? Spanish tends to lengthen — flag if the translation is over 1.5x the EN word count.

## String 4 — Header brand "back to the wall"

**Source key:** `header.brand.label`

**English:**
> Back to the wall

**Spanish:** Volver al muro

**Reviewer prompts:**

- [ ] Is "Volver al muro" idiomatic, or should it be "Regresar al muro" / "Ir al muro"?
- [ ] Does "muro" carry the right metaphor in MX Spanish, or does it evoke border-wall connotations that the brand should carefully avoid?
- [ ] Alternative: "el mapa" (the map), "el recorrido" (the journey)? The brand metaphor IS the wall, but reviewer should confirm the loaded political reading does not occlude the editorial intent.

---

## How to use

1. Native Spanish reviewer reads each string in context (run `npm run dev` and visit `/?lang=es`, then visit a 404 + 500 page).
2. Answer each prompt with yes / no / suggestion.
3. File a single issue tagged `i18n-review` with all "no" + suggestions; W4's Spanish-parity pass picks it up.
4. Sign off below when all prompts are addressed.

## Sign-off

- Reviewer name: _________________________
- Locale (es-MX / es-US / es-ES): _________
- Date: ____________
- Status: [ ] Approved   [ ] Needs revision (file issue link below)
- Issue link (if needed): ________________

---

> Authored 2026-04-28 by W1 Driver-D maximization pass.  
> Source-of-truth EN strings live at `frontend/src/lib/translations/en.json`.  
> Source-of-truth ES strings live at `frontend/src/lib/translations/es.json`.

---

## W2 Driver C — Chapter 4–5 review queue (added 2026-04-28)

The chapters are where editorial gravity lands. Strings flagged below carry an explicit `[ES-pending-review]` suffix in `es.json` and require a native reviewer pass before W4.

### String 5 — Chapter 4 lede (the math thesis)

**Source key:** `wall.chapter04.lede`

**English:**
> Most workforce sites pretend barriers don't matter. We do the math to prove they do.

**Spanish (pending review):**
> La mayoría de los sitios laborales hace como si las barreras no importaran. Nosotros hacemos las cuentas para demostrar que sí.

**Reviewer prompts:**
- [ ] Does "hace como si" capture the contemptuous "pretend"? Alternative: "actúa como si".
- [ ] "Hacemos las cuentas" — financial idiom or can it land for non-monetary barriers?
- [ ] Should "barreras" (barriers) be "obstáculos" for warmer connotation in MX Spanish?

### String 6 — Carlos quote (Ch4a "$300 and a daughter")

**Source key:** `wall.chapter04a.pullquote`

**English:**
> I came home with $300 and a daughter, and the system told me to go to five offices.

**Spanish (pending review):**
> Volví a casa con 300 dólares y una hija, y el sistema me mandó a cinco oficinas.

**Reviewer prompts:**
- [ ] Does "Volví a casa" preserve the "came home from incarceration" subtext?
- [ ] Is "el sistema me mandó" register-correct (formal-warm), or should it be "el sistema me dijo que fuera"?
- [ ] Does the line feel like Carlos's voice (not narrator's)?

### String 7 — Carlos quote (Ch4b "45 minutes is the schedule, 87 is the day")

**Source key:** `wall.chapter04b.pullquote`

**English:**
> Forty-five minutes is the schedule. Eighty-seven is the day.

**Spanish (pending review):**
> Cuarenta y cinco minutos es el horario. Ochenta y siete es el día.

**Reviewer prompts:**
- [ ] Does the Spanish preserve the rhythmic two-clause structure? It should land like a sigh.
- [ ] "El día" — confirm this lands as "the actual day," not "today."

### String 8 — Carlos quote (Ch4d credit door metaphor)

**Source key:** `wall.chapter04d.pullquote`

**English:**
> A score I can't see is closing doors I never knocked on.

**Spanish (pending review):**
> Un puntaje que no veo me está cerrando puertas a las que nunca toqué.

**Reviewer prompts:**
- [ ] Does "puntaje" land for credit score, or should it be "calificación"?
- [ ] The "knock on doors" metaphor: does it work in MX Spanish or read awkwardly?
- [ ] Should the tense be present-perfect ("he tocado") instead of preterite ("toqué")?

### String 9 — Chapter 5 Labyrinth editorial (locked phrase)

**Source key:** `wall.chapter05.editorial`

**English:**
> 5 offices. 47 forms. Each one says go to the next one.

**Spanish (current — NOT flagged, but verify):**
> 5 oficinas. 47 formularios. Cada una te manda a la siguiente.

**Reviewer prompts:**
- [ ] Does "te manda" preserve the bureaucratic command tone? Alternative: "te envía".
- [ ] "La siguiente" agrees with "oficina" (feminine). Confirm intent — is the next OFFICE the antecedent, not the next FORM?
- [ ] Word count: ES is shorter here (good); does the rhythm still feel staccato?

### Locked DO-NOT-translate items (W2 Driver C)

These render as literal numbers / units and stay identical across locales:
- "47" (forms count)
- "5" (offices count)
- "$1,200/mes" — uses `mes` instead of `mo` for ES (already done)
- Bus route names ("Autobús 4", "Autobús 6")

> Authored 2026-04-28 by W2 Driver C — Chapter 4–5 lane.
