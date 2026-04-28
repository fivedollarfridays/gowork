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
