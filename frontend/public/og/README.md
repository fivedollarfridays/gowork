# Static OG fallback gallery

This directory is the rescue gallery for `/api/og/[chapter]`. When the
Edge runtime's Satori-backed `ImageResponse` errors (cold start, font
miss, memory cap), the route 307-redirects to `/og/<chapter>.png` and
the static PNG ships from this directory.

## Generating the PNGs

The PNGs are not committed — Satori output is large and changes whenever
chapter copy or branding changes. They are generated on demand:

```bash
# Terminal 1: start the dev server
cd frontend
npm run dev

# Terminal 2: hit each /api/og/<chapter> route and save the PNG
cd frontend
node scripts/generate-static-og.mjs
```

This writes `1.png` through `10.png` plus `default.png` to this
directory at 1200×630.

## Locale variants

The script supports `--locale es` to capture the Spanish-locale cards.
By default it captures English. If you need both, run twice with
different `--out` directories or rename outputs after each run.

## Why the PNGs are not committed

- They are binary, ~80–200 KB each, total ~2 MB.
- They change whenever chapter copy / branding tokens change.
- Vercel's deploy step runs `npm run build`; we'd rather rebuild the
  cards from source than ship stale fallbacks.

If you want pre-deploy belt-and-suspenders, run the script in CI before
`vercel deploy` and let Vercel pick the static files up as part of
`public/`.

## When the fallback fires

The `/api/og/[chapter]/route.ts` file wraps `new ImageResponse(...)` in
try/catch:

```ts
try {
  return new ImageResponse(tree, { width, height, headers });
} catch (err) {
  return Response.redirect(`${origin}/og/${chapter}.png`, 307);
}
```

If the static PNG isn't present (you forgot to run
`generate-static-og.mjs`), the redirect 404s and the unfurl shows
nothing. That is strictly better than a corrupted Satori output, so the
fallback chain is: Satori → static PNG → no card.

## References

- Generator: `frontend/scripts/generate-static-og.mjs`
- Route: `frontend/src/app/api/og/[chapter]/route.ts`
- Composer: `frontend/src/lib/og/cardComposer.ts`
- Take plan rescue notes: `docs/submission-video-take-plan.md`
- Demo backup paths: `docs/submission-demo.md` Section 2

> Authored W5 Driver B. Branch: `sprint/w5-submission` →
> `w5-driver-b/demo-video-script`.
